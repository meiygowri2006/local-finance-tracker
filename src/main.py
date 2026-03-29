import os
from src.drive_api import download_latest_backup
from src.parser import parse_sms
from src.analyzer import analyze_monthly_spending
from src.sheets_api import push_to_sheets

def main():
    print("\n=======================================")
    print("   LOCAL FINANCE TRACKER INITIALIZED   ")
    print("=======================================\n")
    
    sheet_name = "My Finance Tracker" 
    target_file = "data/raw/sms_backup.xml"
    
    # --- Interactive Menu ---
    print("Where should we get the latest bank messages from?")
    print("  [1] Google Drive (Download latest backup)")
    print("  [2] Local Folder (Read existing file in data/raw/)")
    
    choice = ""
    while choice not in ['1', '2']:
        choice = input("\nEnter 1 or 2: ").strip()
        
        if choice not in ['1', '2']:
            print("Invalid choice. Please type 1 or 2.")

    # --- Execute Based on Choice ---
    if choice == '1':
        success = download_latest_backup(target_file)
        if not success:
            print("      -> Exiting due to download failure.")
            return
    elif choice == '2':
        print(f"\n[0/3] Bypassing Drive. Using local file: {target_file}")
        if not os.path.exists(target_file):
            print(f"      -> ❌ Error: Could not find {target_file}.")
            print("      -> Please place your XML backup in the data/raw/ folder and try again.")
            return

    # 1. Parse
    print("\n[1/3] Reading SMS data...")
    raw_data = parse_sms(target_file)
    if raw_data is None or raw_data.empty:
        print("      -> No data found. Exiting.")
        return

    # 2. Analyze
    print("[2/3] Crunching the numbers...")
    summary_data = analyze_monthly_spending(raw_data)
    if summary_data is None or summary_data.empty:
        print("      -> Math failed. Exiting.")
        return

    # 3. Upload
    print("[3/3] Syncing with Google Sheets...")
    push_to_sheets(raw_data, summary_data, sheet_name)
    
    print("\n=======================================")
    print("          SYNC COMPLETE! 🎉            ")
    print("=======================================\n")

if __name__ == "__main__":
    main()