import os
from src.drive_api import download_latest_backup
from src.parser import parse_sms, parse_pdf  # <--- IMPORT THE NEW FUNCTION
from src.analyzer import analyze_monthly_spending
from src.sheets_api import push_to_sheets

def main():
    print("\n=======================================")
    print("   LOCAL FINANCE TRACKER INITIALIZED   ")
    print("=======================================\n")
    
    sheet_name = "My Finance Tracker" 
    target_file = "data/raw/sms_backup.xml"
    is_pdf = False
    pdf_password = "" # Leave blank if no password, or put your bank password here
    
    # --- Interactive Menu ---
    print("Where should we get the latest data from?")
    print("  [1] Google Drive (Download latest SMS backup)")
    print("  [2] Local Folder (Read SMS XML in data/raw/)")
    print("  [3] PDF Statement (Read statement.pdf in data/raw/)")
    
    choice = ""
    while choice not in ['1', '2', '3']:
        choice = input("\nEnter 1, 2, or 3: ").strip()

    # --- Execute Based on Choice ---
    if choice == '1':
        success = download_latest_backup(target_file)
        if not success: return
        
    elif choice == '2':
        print(f"\n[0/3] Using local SMS file: {target_file}")
        if not os.path.exists(target_file):
            print("      -> ❌ Error: File not found.")
            return
            
    elif choice == '3':
        target_file = "data/raw/statement.pdf"
        is_pdf = True
        print(f"\n[0/3] Using local PDF file: {target_file}")
        if not os.path.exists(target_file):
            print("      -> ❌ Error: Could not find statement.pdf.")
            print("      -> Please place your PDF in the data/raw/ folder and rename it to statement.pdf.")
            return

    # 1. Parse Data
    print("\n[1/3] Reading data...")
    if is_pdf:
        # Use the PDF engine
        raw_data = parse_pdf(target_file, password=pdf_password if pdf_password else None)
    else:
        # Use the SMS engine
        raw_data = parse_sms(target_file)

    if raw_data is None or raw_data.empty:
        print("      -> No data found. Exiting.")
        return

    # 2. Analyze
    print("[2/3] Crunching the numbers...")
    summary_data = analyze_monthly_spending(raw_data)

    # 3. Upload
    print("[3/3] Syncing with Google Sheets...")
    push_to_sheets(raw_data, summary_data, sheet_name)
    
    print("\n=======================================")
    print("          SYNC COMPLETE! 🎉            ")
    print("=======================================\n")

if __name__ == "__main__":
    main()