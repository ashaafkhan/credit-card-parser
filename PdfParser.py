

import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import re
import pandas as pd
import os
import sys
import argparse
DEFAULT_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def configure_tesseract_cmd():
    env_cmd = os.environ.get('TESSERACT_CMD')
    if env_cmd:
        pytesseract.pytesseract.tesseract_cmd = env_cmd
        return
    if os.path.isfile(DEFAULT_TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = DEFAULT_TESSERACT_PATH
        return
    try:
        import subprocess
        proc = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
        if proc.returncode == 0:
            pytesseract.pytesseract.tesseract_cmd = 'tesseract'
            return
    except Exception:
        pass
    print(f"❌ Tesseract not found. Install or set TESSERACT_CMD environment variable.")
    sys.exit(1)

BANK_PATTERNS = {
    "HDFC Bank": {
            "last_4_digits": r"\(.*?(\d{4})\)|(?:\*{4}|X{4}|XXXX)\s*(\d{4})",
            "billing_cycle": r"Statement Period\s*[:\-]?\s*(\d{1,2}\s\w{3,9}\s\d{4})\s*[-to–—]+\s*(\d{1,2}\s\w{3,9}\s\d{4})",
            "payment_due_date": r"Payment Due Date\s*[:\-]?\s*(\d{1,2}\s\w{3,9}\s\d{4})",
            "total_outstanding_balance": r"Total\s*Amount\s*Due\s*[:\-]?\s*(?:INR|Rs\.|₹)?\s*([\d,]+\.?\d{0,2})"
        },
    "ICICI Bank": {
        "last_4_digits": r"Card Number\s*[:\-]?\s*(?:XXXX|\*{4})\s*(\d{4})",
        "billing_cycle": r"Statement Period\s*[:\-]?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})\s*to\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})",
        "payment_due_date": r"Payment Due Date\s*[:\-]?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})",
        "total_outstanding_balance": r"Total Outstanding\s*[:\-]?\s*(?:INR|₹)?\s*([\d,]+\.\d{2})"
    },
    "SBI Card": {
        "last_4_digits": r"Card Number\s*[:\-]?\s*(?:XXXX|\*{4})\s*(\d{4})",
        "billing_cycle": r"Statement Date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})\s*to\s*(\d{2}/\d{2}/\d{4})",
        "payment_due_date": r"Due Date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        "total_outstanding_balance": r"Total Due\s*[:\-]?\s*(?:INR|₹)?\s*([\d,]+\.\d{2})"
    },
    "Axis Bank": {
        "last_4_digits": r"Card Number\s*[:\-]?\s*(?:XXXX|\*{4})\s*(\d{4})",
        "billing_cycle": r"Statement Period\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})\s*[-]\s*(\d{2}/\d{2}/\d{4})",
        "payment_due_date": r"Payment Due Date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        "total_outstanding_balance": r"Amount Due\s*[:\-]?\s*(?:INR|₹)?\s*([\d,]+\.\d{2})"
    },
    "Canara Bank": {
        "last_4_digits": r"Card Number\s*Ending\s*[:\-]?\s*(\d{4})",
        "billing_cycle": r"Billing Period\s*[:\-]?\s*(\d{2}-\d{2}-\d{4})\s*to\s*(\d{2}-\d{2}-\d{4})",
        "payment_due_date": r"Payment Due Date\s*[:\-]?\s*(\d{2}-\d{2}-\d{4})",
        "total_outstanding_balance": r"Outstanding Amount\s*[:\-]?\s*(?:INR|₹)?\s*([\d,]+\.\d{2})"
    }
}


def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except:
        pass

    if not text.strip():
        print(f"⚠️ OCR fallback for {os.path.basename(pdf_path)}")
        images = convert_from_path(pdf_path)
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"

   
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def parse_credit_card_statement(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    result = {
        "issuer": None,
        "last_4_digits": None,
        "billing_cycle_start": None,
        "billing_cycle_end": None,
        "payment_due_date": None,
        "total_outstanding_balance": None
    }

    # Detect bank issuer
    for bank in BANK_PATTERNS.keys():
        if re.search(bank.split()[0], text, re.IGNORECASE):
            result["issuer"] = bank
            patterns = BANK_PATTERNS[bank]
            break
    else:
        print(f"⚠️ Could not detect issuer for {os.path.basename(pdf_path)}")
        return result

    # Extract fields
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if key == "billing_cycle":
                result["billing_cycle_start"] = match.group(1)
                result["billing_cycle_end"] = match.group(2)
            elif key == "total_outstanding_balance":
                result[key] = match.group(1).replace(",", "")
            else:
                result[key] = match.group(1)

    # Generic fallbacks if any field missing
  
    if not result.get("last_4_digits"):
        # Common masked patterns: **** 1234 or XXXX1234 or ends with 1234
        m = re.search(r"(?:\*{4}|X{4}|XXXX|\sX{4}|\*\*\*\*|ending\s*:?)\s*(\d{4})", text, re.IGNORECASE)
        if m:
            result["last_4_digits"] = m.group(1)
        else:
            # fallback: find any 4-digit group that appears near words 'Card' or 'Account'
            m2 = re.search(r"(Card|Account|Ending).{0,30}(\d{4})", text, re.IGNORECASE)
            if m2:
                result["last_4_digits"] = m2.group(2)

    if not result.get("total_outstanding_balance"):
        # Look for common totals: 'Total Due', 'Amount Due', 'Total Outstanding', 'Statement Balance'
        m = re.search(r"(?:Total\s*Due|Amount\s*Due|Total\s*Outstanding|Statement\s*Balance|Current\s*Balance)\s*[:\-]?\s*(?:INR|Rs\.|₹)?\s*([\d,]+\.?\d{0,2})", text, re.IGNORECASE)
        if m:
            # normalize to two decimals if possible
            val = m.group(1).replace(',', '')
            if '.' not in val:
                val = val + '.00'
            result["total_outstanding_balance"] = val

    # Billing cycle and payment date fallbacks (generic month-name patterns)
    if not result.get('billing_cycle_start') or not result.get('billing_cycle_end'):
        mb = re.search(r"(\d{1,2}\s\w{3,9}\s\d{4})\s*[-to–—]+\s*(\d{1,2}\s\w{3,9}\s\d{4})", text)
        if mb:
            result['billing_cycle_start'] = mb.group(1)
            result['billing_cycle_end'] = mb.group(2)

    if not result.get('payment_due_date'):
        mp = re.search(r"Payment\s*Due\s*Date\s*[:\-]?\s*(\d{1,2}\s\w{3,9}\s\d{4})", text, re.IGNORECASE)
        if mp:
            result['payment_due_date'] = mp.group(1)
        else:
            # try other common phrasing
            mp2 = re.search(r"Due\s*Date\s*[:\-]?\s*(\d{1,2}\s\w{3,9}\s\d{4})", text, re.IGNORECASE)
            if mp2:
                result['payment_due_date'] = mp2.group(1)

    return result


# Process multiple PDFs

def process_pdf_list(pdf_paths, out_csv="parsed_credit_card_statements.csv", out_json="parsed_credit_card_statements.json"):
    results = []
    for pdf_path in pdf_paths:
        if not os.path.isfile(pdf_path):
            print(f"⚠️ Skipping missing file: {pdf_path}")
            continue
        print(f"Parsing: {os.path.basename(pdf_path)}")
        data = parse_credit_card_statement(pdf_path)
        results.append(data)

    # Save outputs
    df = pd.DataFrame(results)
    df.to_csv(out_csv, index=False)
    df.to_json(out_json, orient='records', indent=2)
    print(f"✅ Parsing complete. CSV saved to {out_csv} and JSON saved to {out_json}.")


# Main function

def main(argv=None):
    parser = argparse.ArgumentParser(description="Parse credit card statements from a folder or single PDF.")
    parser.add_argument('path', nargs='?', default='credit_statements', help='Folder or PDF file path')
    parser.add_argument('--out-csv', default='parsed_credit_card_statements.csv', help='CSV output file')
    parser.add_argument('--out-json', default='parsed_credit_card_statements.json', help='JSON output file')
    args = parser.parse_args(argv)

    configure_tesseract_cmd()

    input_path = args.path
    pdfs = []
    if os.path.isdir(input_path):
        for file in os.listdir(input_path):
            if file.lower().endswith('.pdf'):
                pdfs.append(os.path.join(input_path, file))
    elif os.path.isfile(input_path) and input_path.lower().endswith('.pdf'):
        pdfs = [input_path]
    else:
        print(f"❌ Path not found or unsupported: {input_path}")
        return

    process_pdf_list(pdfs, out_csv=args.out_csv, out_json=args.out_json)

if __name__ == "__main__":
    main()
