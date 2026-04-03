import fitz  # PyMuPDF
import pandas as pd
import re
from collections import defaultdict
import xml.etree.ElementTree as ET  # Added for parsing the SMS XML

# ─────────────────────────────────────────────
#  CONFIG — Sandbox Calibrations
# ─────────────────────────────────────────────
COL_DATE     = (0,   135)
COL_DETAILS  = (135, 270)
COL_DEBITS   = (270, 368)
COL_CREDITS  = (368, 465)
COL_BALANCE  = (465, 900)

DATE_PATTERN = re.compile(r"^\d{2}\s+[A-Za-z]{3}\s+\d{4}$")
JUNK_KEYWORDS = [
    "ACCOUNT", "Account", "Customer", "Branch", "IFSC",
    "Currency", "ACCOUNT ACTIVITY", "For period",
    "Ending Balance", "Total", "Indian Bank",
]

# ─────────────────────────────────────────────
#  PDF HELPER FUNCTIONS 
# ─────────────────────────────────────────────
def _get_column(x):
    """Return column name based on X coordinate."""
    if COL_DATE[0] <= x < COL_DATE[1]: return "Date"
    elif COL_DETAILS[0] <= x < COL_DETAILS[1]: return "Transaction Details"
    elif COL_DEBITS[0] <= x < COL_DEBITS[1]: return "Debits"
    elif COL_CREDITS[0] <= x < COL_CREDITS[1]: return "Credits"
    elif COL_BALANCE[0] <= x < COL_BALANCE[1]: return "Balance"
    return None

def _extract_raw(pdf_path: str, password: str = None) -> pd.DataFrame:
    """Extract words and group by Y coordinate."""
    doc = fitz.open(pdf_path)
    if doc.is_encrypted and password:
        doc.authenticate(password)
        
    all_rows = []
    for page in doc:
        words = page.get_text("words")
        line_map = defaultdict(lambda: defaultdict(list))
        
        for x0, y0, x1, y1, word, *_ in words:
            y_key = round(y0 / 4) * 4
            col = _get_column(x0)
            if col:
                line_map[y_key][col].append(word)

        for y in sorted(line_map.keys()):
            row = line_map[y]
            all_rows.append({
                "Date": " ".join(row.get("Date", [])),
                "Transaction Details": " ".join(row.get("Transaction Details", [])),
                "Debits": " ".join(row.get("Debits", [])),
                "Credits": " ".join(row.get("Credits", [])),
                "Balance": " ".join(row.get("Balance", [])),
            })
    doc.close()
    df = pd.DataFrame(all_rows)
    if not df.empty:
        df = df[df.apply(lambda r: any(str(v).strip() for v in r), axis=1)]
    return df.reset_index(drop=True)

def _normalize_amount(val) -> str:
    """Strip INR and formatting."""
    t = str(val).strip()
    if not t: return ""
    t = re.sub(r"\bINR\b", "", t, flags=re.I)
    t = re.sub(r"\s+", "", t)
    if not t or t in ("-", "-INR"): return ""
    t = re.sub(r"[^\d.,\-]", "", t)
    if not t or t == "-": return ""
    return t

def _is_valid_date(val: str) -> bool:
    return bool(DATE_PATTERN.match(val.strip()))

def _is_junk_row(row: pd.Series) -> bool:
    date_val = str(row["Date"]).strip()
    details_val = str(row["Transaction Details"]).strip()
    return any(kw in date_val or kw in details_val for kw in JUNK_KEYWORDS)

def _clean_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Remove noise and stitch multi-line details."""
    cleaned = []
    for _, row in df.iterrows():
        if _is_junk_row(row): continue

        if str(row["Date"]).strip() == "Date":
            continuation = str(row["Transaction Details"]).strip()
            if continuation and continuation != "Transaction Details" and cleaned:
                cleaned[-1]["Transaction Details"] += " " + continuation
            continue

        if _is_valid_date(str(row["Date"])):
            cleaned.append(row.to_dict())

    result = pd.DataFrame(cleaned)
    if result.empty:
        return result

    result["Debits"] = result["Debits"].apply(_normalize_amount)
    result["Credits"] = result["Credits"].apply(_normalize_amount)
    result["Transaction Details"] = result["Transaction Details"].str.replace(r"\s+", " ", regex=True).str.strip()
    return result.reset_index(drop=True)


# ─────────────────────────────────────────────
#  MAIN ENTRY POINTS FOR DASHBOARD
# ─────────────────────────────────────────────

def parse_pdf(filepath, password=None):
    """
    Extracts data using PyMuPDF and formats it for the dashboard.
    """
    try:
        raw_df = _extract_raw(filepath, password)
        if raw_df.empty:
            return pd.DataFrame()
            
        clean_df = _clean_csv(raw_df)
        if clean_df.empty:
            return pd.DataFrame()

        dashboard_data = []
        for _, row in clean_df.iterrows():
            date_val = pd.to_datetime(row["Date"], format='mixed', dayfirst=True, errors='coerce')
            desc = row["Transaction Details"]
            
            amount = 0.0
            status = ""

            if row["Debits"]:
                amount = float(row["Debits"].replace(',', ''))
                status = "DEBIT"
            elif row["Credits"]:
                amount = float(row["Credits"].replace(',', ''))
                status = "CREDIT"

            if status and pd.notna(date_val):
                dashboard_data.append({
                    "Date": date_val,
                    "Description": desc,
                    "Amount": amount,
                    "Status": status
                })

        return pd.DataFrame(dashboard_data)

    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return pd.DataFrame()


def parse_sms(filepath):
    """
    Parses Android SMS XML backup, extracting financial transactions.
    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        transactions = []
        
        # Loop through all SMS messages in the XML
        for sms in root.findall('sms'):
            body = sms.get('body', '')
            date_str = sms.get('readable_date', '')
            
            # Basic keyword filter to find financial messages
            body_lower = body.lower()
            if any(keyword in body_lower for keyword in ['debited', 'credited', 'rs.', 'inr', 'ac ', 'a/c']):
                
                amount = 0.0
                status = ""
                
                # Look for amounts (e.g., Rs. 500, INR 1000.50)
                amount_match = re.search(r'(?:rs\.?|inr)\s*([\d,]+\.?\d*)', body_lower)
                if amount_match:
                    try:
                        amount = float(amount_match.group(1).replace(',', ''))
                    except ValueError:
                        continue
                        
                    # Determine if it was money in or money out
                    if 'debited' in body_lower or 'spent' in body_lower or 'deducted' in body_lower:
                        status = "DEBIT"
                    elif 'credited' in body_lower or 'received' in body_lower or 'added' in body_lower:
                        status = "CREDIT"
                        
                    if status and amount > 0:
                        date_val = pd.to_datetime(date_str, errors='coerce')
                        
                        transactions.append({
                            "Date": date_val,
                            "Description": body[:100] + "..." if len(body) > 100 else body, # Keep it clean
                            "Amount": amount,
                            "Status": status
                        })
                        
        return pd.DataFrame(transactions)

    except Exception as e:
        print(f"Error parsing SMS XML: {e}")
        return pd.DataFrame()