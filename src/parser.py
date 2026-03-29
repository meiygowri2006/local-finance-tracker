import re
import pandas as pd

def parse_sms(file_path):
    transactions = []
    
    # These rules teach Python how to find the specific words in the text
    status_pattern = re.compile(r'(debited|credited)', re.IGNORECASE)
    amount_pattern = re.compile(r'(?:INR|Rs\.?)\s*([\d,]+\.\d{2})', re.IGNORECASE)
    date_pattern = re.compile(r'(\d{2}-[A-Za-z]{3}-\d{2})')

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            msg = line.strip()
            if not msg:
                continue
            
            # Search the text using our rules
            status_match = status_pattern.search(msg)
            amount_match = amount_pattern.search(msg)
            date_match = date_pattern.search(msg)

            if status_match and amount_match and date_match:
                status = status_match.group(1).upper()
                # Remove commas from thousands so Python can do math with it
                amount = float(amount_match.group(1).replace(',', ''))
                date = date_match.group(1)

                transactions.append({
                    "Date": date,
                    "Status": status,
                    "Amount": amount
                })

    # Convert the list into a pandas DataFrame (a virtual spreadsheet)
    return pd.DataFrame(transactions)

# This block runs the test
if __name__ == "__main__":
    test_file = "data/raw/bank_messages.txt"
    print("--- Reading Bank Messages ---\n")
    
    df = parse_sms(test_file)
    
    if not df.empty:
        print(df.to_string(index=False))
    else:
        print("No transactions found. Check your text file!")