import streamlit as st
import tempfile
import os
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
else:
    # Preset default display info
    st.sidebar.markdown("---")
    st.sidebar.subheader("Preset details:")
    if preset == "screen":
        st.sidebar.info("• **DPI Limit**: 72 (low res)\n• **JPEG Quality**: 40%\n• **Grayscale**: Yes\n• *Ideal for fast sharing / mobile.*")
        jpeg_quality, dpi_value, force_grayscale = 40, 72, True
    elif preset == "ebook":
        st.sidebar.info("• **DPI Limit**: 150 (medium res)\n• **JPEG Quality**: 65%\n• **Grayscale**: No\n• *Ideal for reading on screens.*")
        jpeg_quality, dpi_value, force_grayscale = 65, 150, False
    else:  # print
        st.sidebar.info("• **DPI Limit**: 300 (high res)\n• **JPEG Quality**: 85%\n• **Grayscale**: No\n• *Ideal for high-res printing.*")
        jpeg_quality, dpi_value, force_grayscale = 85, 300, False

# Main Area
uploaded_file = st.file_uploader("Choose a PDF file to compress", type=["pdf"])

if uploaded_file is not None:
    # Display details of uploaded file
    file_details = {
        "Filename": uploaded_file.name,
        "Original Size": f"{uploaded_file.size / (1024 * 1024):.2f} MB"
    }
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Filename:** `{file_details['Filename']}`")
    with col2:
        st.markdown(f"**Original Size:** `{file_details['Original Size']}`")
        
    st.markdown("---")
    
    if st.button("🚀 Start Compression", use_container_width=True):
        progress_text = "Optimizing and compressing PDF. Please wait..."
        with st.status(progress_text) as status:
            try:
                # Create temporary files for input and output
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_in:
                    tmp_in.write(uploaded_file.getvalue())
                    tmp_in_path = tmp_in.name
                
                tmp_out_path = tmp_in_path.replace(".pdf", "_compressed.pdf")
                
                # Perform the compression
                stats = compress_pdf(
                    input_path=tmp_in_path,
                    output_path=tmp_out_path,
                    preset=None if preset == "custom" else preset,
                    jpeg_quality=jpeg_quality,
                    max_dpi=dpi_value,
                    force_grayscale=force_grayscale
                )
                
                # Read compressed PDF back
                with open(tmp_out_path, "rb") as f:
                    compressed_data = f.read()
                
                # Cleanup temp files
                os.remove(tmp_in_path)
                os.remove(tmp_out_path)
                
                status.update(label="Compression Completed!", state="complete", expanded=False)
                
                # Store data in session state for down-stream actions (e.g. downloading)
                st.session_state["compressed_data"] = compressed_data
                st.session_state["stats"] = stats
                st.session_state["compressed_filename"] = f"compressed_{uploaded_file.name}"
                
            except Exception as e:
                status.update(label=f"An error occurred during compression.", state="error")
                st.error(f"Error details: {e}")
                
    # If compression has been executed and results are in session state, show download options
    if "compressed_data" in st.session_state:
        stats = st.session_state["stats"]
        
        st.success("🎉 PDF compressed successfully!")
        
        # Display comparison metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Original Size", f"{stats['original_size_kb']/1024:.2f} MB")
        
        # Determine color of delta: green is positive compression
        m2.metric(
            "Compressed Size", 
            f"{stats['compressed_size_kb']/1024:.2f} MB", 
            delta=f"-{stats['savings_percent']:.1f}%",
            delta_color="normal"
        )
        m3.metric("Processing Time", f"{stats['duration_seconds']:.2f}s")
        
        # Download button
        st.download_button(
            label="⬇️ Download Compressed PDF",
            data=st.session_state["compressed_data"],
            file_name=st.session_state["compressed_filename"],
            mime="application/pdf",
            use_container_width=True
        )
        
        # Extra details
        st.info(f"The compressed file is **{stats['savings_percent']:.1f}%** smaller than the original.")
