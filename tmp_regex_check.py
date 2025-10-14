import PdfParser, re
text = PdfParser.extract_text_from_pdf('samples\\Axis_realistic_statement.pdf')
print('---EXTRACTED TEXT---\n')
print(text)
print('\n---TEST PATTERNS---\n')
patterns = [r'Card\s+([A-Za-z0-9 ]+?)\s*\(', r'Card\s+([A-Za-z ]+)\s*\(']
for p in patterns:
    m = re.search(p, text, re.IGNORECASE)
    print('PATTERN:', p)
    print(' MATCH:', bool(m), 'GROUPS:', m.groups() if m else None)
# Additional checks for billing and payment
print('\n---BILLING/PAYMENT CHECKS---')
bill_pattern = r"Statement Period\s*[:\-]?\s*(\d{1,2}\s\w{3,9}\s\d{4})\s*[-to–—]+\s*(\d{1,2}\s\w{3,9}\s\d{4})"
pay_pattern = r"Payment Due Date\s*[:\-]?\s*(\d{1,2}\s\w{3,9}\s\d{4})"
mb = re.search(bill_pattern, text, re.IGNORECASE)
mp = re.search(pay_pattern, text, re.IGNORECASE)
print('BILL MATCH:', bool(mb), 'GROUPS:', mb.groups() if mb else None)
print('PAY MATCH:', bool(mp), 'GROUPS:', mp.groups() if mp else None)

# Show all 'Card (...)' occurrences
cards = re.findall(r"Card\s+([A-Za-z0-9 ]+?)\s*\(.*?(\d{4})\)", text, re.IGNORECASE)
print('\nALL CARD PAREN MATCHES:', cards)
print('\n---PARSE RESULT---')
res = PdfParser.parse_credit_card_statement('samples\\Axis_realistic_statement.pdf')
import json
print(json.dumps(res, indent=2))
