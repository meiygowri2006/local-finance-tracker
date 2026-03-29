import xml.etree.ElementTree as ET
import re
import pandas as pd

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