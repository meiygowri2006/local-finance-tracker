import pandas as pd

def analyze_monthly_spending(raw_data):
    """
    Groups raw transactions by month and calculates Total Spend and Total Credit.
    Returns a DataFrame with columns: ['Month', 'Total Spend', 'Total Credit']
    """
    if raw_data is None or raw_data.empty:
        return pd.DataFrame(columns=['Month', 'Total Spend', 'Total Credit'])
        
    df = raw_data.copy()
    
    # Ensure Date is properly formatted and drop any invalid rows
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Extract the Year-Month (e.g., '2026-01')
    df['Month'] = df['Date'].dt.strftime('%Y-%m')

    # Create a pivot table to sum amounts by Status for each month
    summary = df.pivot_table(
        index='Month', 
        columns='Status', 
        values='Amount', 
        aggfunc='sum', 
        fill_value=0
    ).reset_index()

    # Ensure DEBIT and CREDIT columns exist (in case a month only has one type)
    if 'DEBIT' not in summary.columns:
        summary['DEBIT'] = 0.0
    if 'CREDIT' not in summary.columns:
        summary['CREDIT'] = 0.0

    # Rename columns to match your requested format
    summary = summary.rename(columns={
        'DEBIT': 'Total Spend',
        'CREDIT': 'Total Credit'
    })

    # Return exactly the 3 columns requested
    return summary[['Month', 'Total Spend', 'Total Credit']]