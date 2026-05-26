# PDFEditor

<p align="left">
  <a href="https://www.python.org/" target="_blank"><img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white"/></a>
  <a href="https://streamlit.io/" target="_blank"><img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-1.20%2B-FF4B4B?logo=streamlit&logoColor=white"/></a>
  <a href="https://pymupdf.readthedocs.io/" target="_blank"><img alt="PyMuPDF" src="https://img.shields.io/badge/PyMuPDF-1.22%2B-2E6DB4"/></a>
  <a href="https://python-pillow.org/" target="_blank"><img alt="Pillow" src="https://img.shields.io/badge/Pillow-9.0%2B-8B5CF6"/></a>
</p>

PDFEditor is a lightweight Streamlit app for compressing PDF files locally and quickly. The current goal is rapid prototyping: keep the workflow simple, reduce document size, and avoid sending files to external services.

## What It Does

- Upload one or multiple PDF files from the browser.
- Choose a predefined compression preset or fine-tune custom settings.
- Optimize embedded images and apply structural cleanup to the document.
- Return a compressed PDF per file or a `.zip` when processing multiple files.
- Display size, savings, and processing-time statistics.

## Project Structure

- `app.py`: Streamlit UI and user-flow orchestration.
- `compressor.py`: Compression logic built on top of PyMuPDF and Pillow.
- `requirements.txt`: Project dependencies.
- `run.bat`: Windows shortcut for launching the app.

## Requirements

- Python 3.10 or newer is recommended.
- An activated virtual environment.

## Installation

```bash
pip install -r requirements.txt
```

If you prefer using a virtual environment on Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run the App

### Option 1: direct command

```bash
streamlit run app.py
```

### Option 2: Windows shortcut

```bat
run.bat
```

## Usage

1. Open the app in your browser.
2. Upload one or more PDF files.
3. Choose a preset:
   - `Screen`: high compression.
   - `Ebook`: balanced size and quality.
   - `Print`: higher quality.
   - `Custom Settings`: manual control.
4. Start the compression job.
5. Download the result.

## Compression Settings

In custom mode, you can adjust:

- JPEG quality.
- Maximum image DPI.
- Grayscale conversion.
- Page scale factor.

## Technical Notes

The current compression pipeline focuses on:

- Replacing embedded images when the compressed version is smaller.
- Downsampling images when their effective DPI exceeds the selected limit.
- Rescaling the document if the page scale factor is different from `1.0`.
- Saving the final PDF with cleanup and stream compression enabled.

## Project Status

This repository is intentionally optimized for fast prototyping. The current codebase already separates the UI layer from the compression logic, which makes it easy to evolve into a more formal spec-driven workflow later on.

## Possible Next Steps

- Add tests for the compression logic.
- Move presets and configuration into a dedicated module.
- Improve per-file result tracking and reporting.
- Formalize a feature- or spec-oriented project structure.

