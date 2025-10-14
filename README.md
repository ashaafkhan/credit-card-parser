PDF Parser
==========

Small utility to extract key fields from credit card PDF statements and save results to CSV/JSON. Includes a Tkinter GUI to run parsing and preview results.

Requirements
------------
- Python 3.8+
- Tesseract OCR (for OCR fallback)

Required Python packages (see `requirements.txt`):
- pdfplumber
- pytesseract
- pdf2image
- pandas
- pillow

Install
-------
1. Install Tesseract for Windows:
   - Download and run an installer (for example the UB Mannheim build) and keep note of the installation path (commonly `C:\Program Files\Tesseract-OCR\tesseract.exe`).

2. Create a virtual environment and install Python packages:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Usage
-----
- CLI:

```powershell
# Process a folder
python PdfParser.py credit_statements

# Process a single PDF and write outputs to custom paths
python PdfParser.py samples\Axis_realistic_statement.pdf --out-csv out.csv --out-json out.json
```

- GUI:

```powershell
python pdfparser_gui.py
```

  - Browse to a file or folder, optionally provide Tesseract path or click Detect, set output files, then click Run Parser.
  - Preview results in the GUI and use Save JSON As / Save CSV As to download outputs.

Notes
-----
- Add Tesseract to PATH or set the `TESSERACT_CMD` environment variable if Tesseract is installed in a non-standard location.
- If you run into errors installing `pdf2image`, ensure you have poppler installed and available (see pdf2image docs).

License
-------
MIT
