import pandas as pd
import gspread
from gspread_formatting import *
from google.oauth2.service_account import Credentials

def push_to_sheets(raw_df, summary_df, spreadsheet_name="My Finance Tracker"):
    print("      -> Authenticating and Styling...")
    try:
        creds = Credentials.from_service_account_file('credentials/service_account.json', 
                                                     scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        gc = gspread.authorize(creds)
        sheet = gc.open(spreadsheet_name)
    except Exception as e:
        print(f"      -> ❌ Error connecting to Google Sheets: {e}")
        return

    def format_worksheet(ws, data_df):
        ws.clear()
        
        # 1. Convert dates to plain text strings to prevent JSON errors
        upload_df = data_df.copy()
        for col in upload_df.columns:
            if pd.api.types.is_datetime64_any_dtype(upload_df[col]):
                upload_df[col] = upload_df[col].dt.strftime('%d-%b-%y')
            elif pd.api.types.is_period_dtype(upload_df[col]):
                upload_df[col] = upload_df[col].astype(str)
        
        upload_df = upload_df.fillna("")

        # 2. Insert Headers and Data
        ws.update([upload_df.columns.values.tolist()] + upload_df.values.tolist())
        
        # 3. Apply Formal Font & Bold Headers
        fmt = cellFormat(
            textFormat=textFormat(bold=True, fontFamily="Roboto"),
            backgroundColor=color(0.9, 0.9, 0.9),
            horizontalAlignment='CENTER'
        )
        format_cell_range(ws, 'A1:Z1', fmt)
        
        # 4. Set Column Width and Font for the whole sheet
        set_column_width(ws, 'A:Z', 150)
        format_cell_range(ws, 'A:Z', cellFormat(textFormat=textFormat(fontFamily="Roboto")))

    # --- RAW TRANSACTIONS LOGIC ---
    try:
        raw_ws = sheet.worksheet("Raw_Transactions")
    except:
        raw_ws = sheet.add_worksheet("Raw_Transactions", 1000, 10)
    
    format_worksheet(raw_ws, raw_df)
    
    # Conditional Formatting (Corrected foregroundColor and bold syntax)
    rule_debit = ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('B2:B1000', raw_ws)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_CONTAINS', ['DEBIT']),
            format=cellFormat(textFormat=textFormat(foregroundColor=color(1, 0, 0), bold=True))
        )
    )
    rule_credit = ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('B2:B1000', raw_ws)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_CONTAINS', ['CREDIT']),
            format=cellFormat(textFormat=textFormat(foregroundColor=color(0, 0.5, 0), bold=True))
        )
    )
    rules = get_conditional_format_rules(raw_ws)
    rules.clear() # Clear old rules so they don't stack up forever
    rules.append(rule_debit)
    rules.append(rule_credit)
    rules.save()

    # --- MONTHLY SUMMARY LOGIC ---
    try:
        sum_ws = sheet.worksheet("Monthly_Summary")
    except:
        sum_ws = sheet.add_worksheet("Monthly_Summary", 100, 10)
    
    format_worksheet(sum_ws, summary_df)
    print("      -> ✅ Styled sheets synced successfully.")