import pandas as pd

def analyze_monthly_spending(df):
    if df is None or df.empty:
        return None

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # 1. Calculate Overall Summary
    total_credited = df[df['Status'] == 'CREDIT']['Amount'].sum()
    total_spent = df[df['Status'] == 'DEBIT']['Amount'].sum()
    current_balance = total_credited - total_spent

    # 2. Monthly Breakdown
    spending_df = df[df['Status'] == 'DEBIT'].copy()
    if spending_df.empty:
        return pd.DataFrame({
            "Metric": ["Total Credited", "Total Spent", "Current Balance"],
            "Value": [total_credited, total_spent, current_balance]
        })

    spending_df['Month'] = spending_df['Date'].dt.to_period('M')
    monthly_summary = spending_df.groupby('Month')['Amount'].sum().reset_index()
    monthly_summary.rename(columns={'Amount': 'Total_Spend'}, inplace=True)

    # 3. Combine everything into a clean Summary Table
    summary_data = [
        {"Month": "OVERALL", "Total_Spend": total_spent, "Percentage": "100%", "Note": "Total Account Outflow"},
        {"Month": "BALANCE", "Total_Spend": current_balance, "Percentage": "-", "Note": "Current Net Status"}
    ]
    
    # Add individual months
    for _, row in monthly_summary.iterrows():
        perc = (row['Total_Spend'] / total_spent) * 100
        summary_data.append({
            "Month": str(row['Month']),
            "Total_Spend": row['Total_Spend'],
            "Percentage": f"{perc:.2f}%",
            "Note": "Monthly Expense"
        })

    return pd.DataFrame(summary_data)