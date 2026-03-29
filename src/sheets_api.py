import gspread
from google.oauth2.service_account import Credentials

# These URLs tell Google exactly what permissions our bot is asking for
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def push_to_sheets(raw_df, summary_df, spreadsheet_name="My Finance Tracker"):
    print("      -> Authenticating with Google...")
    try:
        # 1. Wake up the bot using your secret key
        credentials = Credentials.from_service_account_file(
            'credentials/service_account.json', 
            scopes=SCOPES
        )
        gc = gspread.authorize(credentials)

        # 2. Open your specific Google Sheet
        sheet = gc.open(spreadsheet_name)

        # 3. Clean the data (Google Sheets hates empty/NaN values and strict datetime objects)
        raw_df_clean = raw_df.copy()
        raw_df_clean['Date'] = raw_df_clean['Date'].astype(str) # Convert dates to plain text
        raw_df_clean = raw_df_clean.fillna("")
        
        summary_df_clean = summary_df.copy().fillna("")

        # 4. Upload Raw Data
        try:
            raw_worksheet = sheet.worksheet("Raw_Transactions")
        except gspread.exceptions.WorksheetNotFound:
            # If the tab doesn't exist, create it
            raw_worksheet = sheet.add_worksheet(title="Raw_Transactions", rows="1000", cols="10")
        
        raw_worksheet.clear() # Wipe old data
        # Insert headers and data
        raw_worksheet.update([raw_df_clean.columns.values.tolist()] + raw_df_clean.values.tolist())
        print("      -> ✅ Raw Transactions uploaded.")

        # 5. Upload Monthly Summary
        try:
            summary_worksheet = sheet.worksheet("Monthly_Summary")
        except gspread.exceptions.WorksheetNotFound:
            summary_worksheet = sheet.add_worksheet(title="Monthly_Summary", rows="100", cols="10")
        
        summary_worksheet.clear()
        summary_worksheet.update([summary_df_clean.columns.values.tolist()] + summary_df_clean.values.tolist())
        print("      -> ✅ Monthly Summary uploaded.")

    except Exception as e:
        print(f"      -> ❌ Error connecting to Google Sheets: {e}")