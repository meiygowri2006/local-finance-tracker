from src.parser import parse_sms
from src.analyzer import analyze_monthly_spending
from src.sheets_api import push_to_sheets

def main():
    print("\n=======================================")
    print("   LOCAL FINANCE TRACKER INITIALIZED   ")
    print("=======================================\n")
    
    target_file = "data/raw/bank_messages.txt"
    sheet_name = "My Finance Tracker" # Must match exactly what you named it in Google Drive
    
    # 1. Parse
    print("[1/3] Reading SMS data...")
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
    print("[3/3] Syncing with Google Cloud...")
    push_to_sheets(raw_data, summary_data, sheet_name)
    
    print("\n=======================================")
    print("          SYNC COMPLETE! 🎉            ")
    print("=======================================\n")

if __name__ == "__main__":
    main()