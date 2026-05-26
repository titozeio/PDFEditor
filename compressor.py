import fitz  # PyMuPDF
import io
import os
import time
from PIL import Image

def get_file_size_kb(file_path):
    """Returns the file size in Kilobytes."""
    try:
        return os.path.getsize(file_path) / 1024.0
    except OSError:
        return 0.0

def compress_pdf(
    input_path, 
    output_path, 
    preset=None, 
    jpeg_quality=75, 
    max_dpi=150, 
    force_grayscale=False
):
    """
    Compresses a PDF by optimizing images and performing structural cleanup.
    
    Parameters:
        input_path (str): Path to the input PDF file.
        output_path (str): Path to save the compressed PDF file.
        preset (str): Preset name ('screen', 'ebook', 'print', or None/Custom).
        jpeg_quality (int): JPEG quality slider (10 to 100). Used if preset is None.
        max_dpi (int): Maximum image DPI (e.g., 72, 150, 300). Used if preset is None.
        force_grayscale (bool): If True, converts images to grayscale. Used if preset is None.
        
    Returns:
        dict: Compression statistics (original_size, compressed_size, ratio, duration).
    """
    start_time = time.time()
    original_size = get_file_size_kb(input_path)
    
    # Apply presets if selected
    if preset == "screen":
        jpeg_quality = 40
        max_dpi = 72
        force_grayscale = True
    elif preset == "ebook":
        jpeg_quality = 65
        max_dpi = 150
        force_grayscale = False
    elif preset == "print":
        jpeg_quality = 85
        max_dpi = 300
        force_grayscale = False
    
    doc = fitz.open(input_path)
    
    # Iterate through each page to compress images
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        
        for img_info in image_list:
            xref = img_info[0]
            
            # Extract image bytes and info
            try:
                base_image = doc.extract_image(xref)
            except Exception:
                # If extraction fails, skip to next image
                continue
                
            if not base_image:
                continue
                
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            # Load image into Pillow
            try:
                img = Image.open(io.BytesIO(image_bytes))
            except Exception:
                continue
            
            orig_width, orig_height = img.size
            
            # Determine visual dimensions on page to estimate current DPI
            rects = page.get_image_rects(xref)
            if rects:
                rect = rects[0]
                display_width_in = rect.width / 72.0
                display_height_in = rect.height / 72.0
                current_dpi = orig_width / display_width_in if display_width_in > 0 else 150
            else:
                display_width_in = orig_width / 150.0
                display_height_in = orig_height / 150.0
                current_dpi = 150
            
            # Check if resolution exceeds maximum DPI
            need_resize = False
            new_size = (orig_width, orig_height)
            if max_dpi and current_dpi > max_dpi:
                target_width = int(display_width_in * max_dpi)
                target_height = int(display_height_in * max_dpi)
                
                # Only scale down, never scale up
                if 0 < target_width < orig_width and 0 < target_height < orig_height:
                    new_size = (target_width, target_height)
                    need_resize = True
            
            # Grayscale conversion check
            need_grayscale = force_grayscale and img.mode in ("RGB", "RGBA")
            
            # Check if processing is needed
            if need_resize or need_grayscale or jpeg_quality < 100:
                if need_grayscale:
                    img = img.convert("L")
                elif img.mode == "RGBA":
                    # Convert transparent background to white for JPEG compatibility
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    # Check if alpha channel exists in the image
                    alpha_channels = img.split()
                    if len(alpha_channels) >= 4:
                        background.paste(img, mask=alpha_channels[3])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                
                if need_resize:
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save compressed image to bytes
                out_io = io.BytesIO()
                try:
                    img.save(out_io, format="JPEG", quality=jpeg_quality, optimize=True)
                    compressed_bytes = out_io.getvalue()
                    
                    # Only replace if compressed image is smaller than original
                    if len(compressed_bytes) < len(image_bytes):
                        page.replace_image(xref, stream=compressed_bytes)
                except Exception as e:
                    print(f"Error compressing/replacing image {xref}: {e}")
                    
    # Save the final PDF with high level garbage collection and stream compression
    # garbage=4: eliminates unused, duplicate, and redundant objects
    # deflate=True: compresses file streams (text, vector graphics)
    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()
    
    compressed_size = get_file_size_kb(output_path)
    duration = time.time() - start_time
    
    # Calculate savings
    if original_size > 0:
        savings_percent = ((original_size - compressed_size) / original_size) * 100.0
    else:
        savings_percent = 0.0
        
    return {
        "original_size_kb": original_size,
        "compressed_size_kb": compressed_size,
        "savings_percent": savings_percent,
        "duration_seconds": duration
    }
