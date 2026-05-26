import streamlit as st
import tempfile
import os
import zipfile
import io
import time
from compressor import compress_pdf, get_file_size_kb

# Set page configuration
st.set_page_config(
    page_title="PDF Size Optimizer",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom header
st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #4A607A; font-family: 'Outfit', sans-serif;">📄 PDF Size Optimizer</h1>
        <p style="color: #7F8C8D; font-size: 1.1rem;">Compress your PDF documents locally, keeping your data secure.</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar layout for Parameters
st.sidebar.header("⚙️ Compression Settings")

# Selection of compression mode / preset
compression_mode = st.sidebar.selectbox(
    "Select Optimization Level",
    options=["Screen (High Compression)", "Ebook (Medium Compression)", "Print (Low Compression)", "Custom Settings"],
    index=1  # Default to Ebook
)

# Map human-readable selection to preset names
preset_map = {
    "Screen (High Compression)": "screen",
    "Ebook (Medium Compression)": "ebook",
    "Print (Low Compression)": "print",
    "Custom Settings": "custom"
}
preset = preset_map[compression_mode]

# Custom settings input
if preset == "custom":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 Custom Parameters")
    
    jpeg_quality = st.sidebar.slider(
        "JPEG Image Quality",
        min_value=10,
        max_value=100,
        value=75,
        step=5,
        help="Lower values reduce quality but decrease file size significantly."
    )
    
    max_dpi = st.sidebar.selectbox(
        "Maximum Image Resolution (DPI)",
        options=[72, 100, 150, 200, 300, "Keep Original"],
        index=2,  # Defaults to 150
        help="Downsamples images exceeding this DPI. 150 DPI is recommended for digital reading."
    )
    # Convert 'Keep Original' to None
    dpi_value = None if max_dpi == "Keep Original" else max_dpi
    
    force_grayscale = st.sidebar.checkbox(
        "Convert Images to Grayscale",
        value=False,
        help="Check this if the PDF is black and white or color doesn't matter (reduces size further)."
    )
    
    page_scale_pct = st.sidebar.number_input(
        "Page Scale Factor (%)",
        min_value=10,
        max_value=200,
        value=100,
        step=5,
        help="Scales the physical dimensions of the pages. Min 10%, Max 200%."
    )
    
    if page_scale_pct < 10 or page_scale_pct > 200:
        st.sidebar.error("❌ Error: El factor de escala debe estar entre 10% y 200%.")
        st.stop()
        
    page_scale = page_scale_pct / 100.0
else:
    # Preset default display info
    st.sidebar.markdown("---")
    st.sidebar.subheader("Preset details:")
    if preset == "screen":
        st.sidebar.info("• **DPI Limit**: 72 (low res)\n• **JPEG Quality**: 40%\n• **Grayscale**: Yes\n• *Ideal for fast sharing / mobile.*")
        jpeg_quality, dpi_value, force_grayscale, page_scale = 40, 72, True, 1.0
    elif preset == "ebook":
        st.sidebar.info("• **DPI Limit**: 150 (medium res)\n• **JPEG Quality**: 65%\n• **Grayscale**: No\n• *Ideal for reading on screens.*")
        jpeg_quality, dpi_value, force_grayscale, page_scale = 65, 150, False, 1.0
    else:  # print
        st.sidebar.info("• **DPI Limit**: 300 (high res)\n• **JPEG Quality**: 85%\n• **Grayscale**: No\n• *Ideal for high-res printing.*")
        jpeg_quality, dpi_value, force_grayscale, page_scale = 85, 300, False, 1.0

# Main Area
uploaded_files = st.file_uploader("Choose PDF files to compress", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    # Build list of file details
    files_data = []
    for f in uploaded_files:
        files_data.append({
            "File Name": f.name,
            "Original Size": f"{f.size / (1024 * 1024):.2f} MB"
        })
    
    st.write(f"📂 **Selected Files ({len(uploaded_files)}):**")
    st.dataframe(files_data, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    if st.button("🚀 Start Compression Job", use_container_width=True):
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        
        compressed_results = []
        total_original_kb = 0
        total_compressed_kb = 0
        overall_start_time = time.time()
        
        # Clear previous session state
        if "job_results" in st.session_state:
            del st.session_state["job_results"]
        
        for idx, uploaded_file in enumerate(uploaded_files):
            status_text.markdown(f"**Processing {idx+1}/{len(uploaded_files)}:** `{uploaded_file.name}`...")
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_in:
                tmp_in.write(uploaded_file.getvalue())
                tmp_in_path = tmp_in.name
                
            tmp_out_path = tmp_in_path.replace(".pdf", "_compressed.pdf")
            
            try:
                stats = compress_pdf(
                    input_path=tmp_in_path,
                    output_path=tmp_out_path,
                    preset=None if preset == "custom" else preset,
                    jpeg_quality=jpeg_quality,
                    max_dpi=dpi_value,
                    force_grayscale=force_grayscale,
                    page_scale=page_scale
                )
                
                with open(tmp_out_path, "rb") as f_out:
                    comp_bytes = f_out.read()
                    
                compressed_results.append({
                    "filename": uploaded_file.name,
                    "bytes": comp_bytes,
                    "original_size_kb": stats["original_size_kb"],
                    "compressed_size_kb": stats["compressed_size_kb"],
                    "savings_percent": stats["savings_percent"],
                    "success": True
                })
                
                total_original_kb += stats["original_size_kb"]
                total_compressed_kb += stats["compressed_size_kb"]
                
            except Exception as e:
                compressed_results.append({
                    "filename": uploaded_file.name,
                    "success": False,
                    "error": str(e)
                })
            finally:
                if os.path.exists(tmp_in_path):
                    os.remove(tmp_in_path)
                if os.path.exists(tmp_out_path):
                    os.remove(tmp_out_path)
                    
            progress_bar.progress((idx + 1) / len(uploaded_files))
            
        overall_duration = time.time() - overall_start_time
        progress_bar.empty()
        status_text.empty()
        
        # Filter successful ones
        successful_results = [r for r in compressed_results if r["success"]]
        
        if successful_results:
            # Store in session state
            st.session_state["job_results"] = compressed_results
            st.session_state["total_orig_kb"] = total_original_kb
            st.session_state["total_comp_kb"] = total_compressed_kb
            st.session_state["job_duration"] = overall_duration
            
            # Prepare download data
            if len(successful_results) == 1:
                # Single file
                st.session_state["download_bytes"] = successful_results[0]["bytes"]
                st.session_state["download_filename"] = f"compressed_{successful_results[0]['filename']}"
                st.session_state["download_mime"] = "application/pdf"
            else:
                # Multiple files: Zip package
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for res in successful_results:
                        zf.writestr(res["filename"], res["bytes"])
                
                st.session_state["download_bytes"] = zip_buffer.getvalue()
                st.session_state["download_filename"] = "compressed_pdfs_job.zip"
                st.session_state["download_mime"] = "application/zip"
        else:
            st.error("❌ None of the files could be compressed.")
            
    # Display results if available in session state
    if "job_results" in st.session_state:
        st.success("🎉 Compression job completed successfully!")
        
        results = st.session_state["job_results"]
        total_orig = st.session_state["total_orig_kb"]
        total_comp = st.session_state["total_comp_kb"]
        duration = st.session_state["job_duration"]
        
        # Overall delta
        if total_orig > 0:
            overall_savings = ((total_orig - total_comp) / total_orig) * 100.0
        else:
            overall_savings = 0.0
            
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Original Size", f"{total_orig / 1024:.2f} MB")
        m2.metric(
            "Total Compressed Size", 
            f"{total_comp / 1024:.2f} MB", 
            delta=f"-{overall_savings:.1f}%",
            delta_color="normal"
        )
        m3.metric("Total Processing Time", f"{duration:.2f}s")
        
        # Details breakdown
        st.markdown("### 📋 Compression Details")
        details_table = []
        for res in results:
            if res["success"]:
                details_table.append({
                    "File Name": res["filename"],
                    "Orig Size (MB)": f"{res['original_size_kb'] / 1024:.2f}",
                    "Comp Size (MB)": f"{res['compressed_size_kb'] / 1024:.2f}",
                    "Savings (%)": f"{res['savings_percent']:.1f}%",
                    "Status": "✅ Success"
                })
            else:
                details_table.append({
                    "File Name": res["filename"],
                    "Orig Size (MB)": "-",
                    "Comp Size (MB)": "-",
                    "Savings (%)": "-",
                    "Status": f"❌ Error ({res['error']})"
                })
        st.dataframe(details_table, use_container_width=True, hide_index=True)
        
        # Download action
        st.download_button(
            label=f"⬇️ Download Compressed Work ({'ZIP Archive' if 'zip' in st.session_state['download_mime'] else 'PDF File'})",
            data=st.session_state["download_bytes"],
            file_name=st.session_state["download_filename"],
            mime=st.session_state["download_mime"],
            use_container_width=True
        )
