import xml.etree.ElementTree as ET
import re
import pandas as pd
import pdfplumber

def parse_sms(file_path):
    transactions = []
    
    # 1. STATUS: Looks for the FIRST action word (Dr, Cr, Transferred, etc.)
    status_pattern = re.compile(r'(debited|transferred|sent|credited|dr\.?|cr\.?)', re.IGNORECASE)
    
    # 2. AMOUNT: Now handles Rs.1 (no decimals) AND Rs.235.00 (decimals)
    amount_pattern = re.compile(r'(?:INR|Rs\.?)\s*([\d,]+(?:\.\d{1,2})?)', re.IGNORECASE)
    
    # 3. DATE: Now handles DD-MM-YYYY, YYYY-MM-DD, and BOB's weird YYYY:MM:DD
    date_pattern = re.compile(r'(\d{2}-\d{2}-\d{4}|\d{4}[:\-]\d{2}[:\-]\d{2})')

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        for sms in root.findall('sms'):
            msg = sms.get('body')
            if not msg: continue
            
            # Find our targets
            status_match = status_pattern.search(msg)
            amount_match = amount_pattern.search(msg)
            date_match = date_pattern.search(msg)

            if status_match and amount_match and date_match:
                raw_status = status_match.group(1).lower()
                
                # Categorize into DEBIT or CREDIT
                if any(word in raw_status for word in ['debited', 'transferred', 'sent', 'dr']):
                    status = "DEBIT"
                else:
                    status = "CREDIT"

                # Clean the amount
                amount = float(amount_match.group(1).replace(',', ''))
                
                # Clean the date (Replace BOB's weird colons with standard hyphens)
                date = date_match.group(1).replace(':', '-')

                transactions.append({
                    "Date": date,
                    "Status": status,
                    "Amount": amount
                })

    except Exception as e:
        print(f"      -> ❌ Error parsing file: {e}")
        return pd.DataFrame()

    return pd.DataFrame(transactions)


def parse_pdf(file_path, password=None):
    """
    Reads a bank statement PDF line by line.
    Note: You may need to adjust the regex based on your specific bank's layout.
    """
    transactions = []
    
    # Looks for DD/MM/YYYY or DD-MM-YYYY
    date_pattern = re.compile(r'(\d{2}[-/]\d{2}[-/]\d{2,4})')
    # Looks for amounts (e.g., 1,500.00)
    amount_pattern = re.compile(r'([\d,]+\.\d{2})')

    try:
        # Open the PDF (handles passwords if provided)
        with pdfplumber.open(file_path, password=password) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text: continue

                for line in text.split('\n'):
                    date_match = date_pattern.search(line)
                    
                    # If a line has a date, it is likely a transaction row
                    if date_match:
                        amounts = amount_pattern.findall(line)
                        if amounts:
                            raw_line = line.lower()
                            
                            # Determine Credit vs Debit
                            # Bank statements usually have Cr for credit. If not, assume Debit.
                            if any(word in raw_line for word in [' cr', 'credit', 'deposit']):
                                status = "CREDIT"
                            else:
                                status = "DEBIT"

                            # Grab the first amount found on the line
                            amount = float(amounts[0].replace(',', ''))
                            date = date_match.group(1).replace('/', '-')

                            transactions.append({
                                "Date": date,
                                "Status": status,
                                "Amount": amount
                            })

    except Exception as e:
        print(f"      -> ❌ Error parsing PDF: {e}")
        return pd.DataFrame()

    return pd.DataFrame(transactions)