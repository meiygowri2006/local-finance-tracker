import pandas as pd

def analyze_monthly_spending(df):
    """
    Takes the raw transaction DataFrame, filters for debits, 
    and calculates monthly spending totals and percentages.
    """
    if df is None or df.empty:
        print("No data to analyze.")
        return None

    # 1. Convert text dates to actual Python datetime objects
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y', errors='coerce')

    # 2. Filter out Credits (we only want to analyze what you spent)
    # UPDATED: Looking specifically for 'DEBITED' to match the parser
    spending_df = df[df['Status'] == 'DEBITED'].copy()

    # Safety check in case there are no debits
    if spending_df.empty:
        print("No debit transactions found to analyze.")
        return spending_df

    # 3. Extract just the Month and Year (e.g., '2026-04')
    spending_df['Month'] = spending_df['Date'].dt.to_period('M')

    # 4. Add up all the spending for each month
    monthly_summary = spending_df.groupby('Month')['Amount'].sum().reset_index()
    monthly_summary.rename(columns={'Amount': 'Total_Spend'}, inplace=True)

    # 5. Calculate percentages
    total_all_spend = monthly_summary['Total_Spend'].sum()
    monthly_summary['Percentage_of_Total'] = (monthly_summary['Total_Spend'] / total_all_spend) * 100
    
    # Clean up the formatting
    monthly_summary['Percentage_of_Total'] = monthly_summary['Percentage_of_Total'].round(2)
    monthly_summary['Month'] = monthly_summary['Month'].astype(str)

    return monthly_summary

# --- Testing Block ---
if __name__ == "__main__":
    # UPDATED: Tell Python exactly where parser.py is located
    from src.parser import parse_sms
    
    test_file = "data/raw/bank_messages.txt"
    print("--- Analyzing Spending Data ---\n")
    
    # 1. Get the raw data
    raw_df = parse_sms(test_file)
    
    # 2. Run the math
    summary_df = analyze_monthly_spending(raw_df)
    
    # 3. Show the results
    if summary_df is not None and not summary_df.empty:
        print(summary_df.to_string(index=False))