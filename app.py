import streamlit as st
import pandas as pd
import os
from src.parser import parse_sms, parse_pdf
from src.analyzer import analyze_monthly_spending
from src.drive_api import download_latest_backup
from src.sheets_api import push_to_sheets

# 1. Setup the Page
st.set_page_config(page_title="My Finance Tracker", layout="wide", page_icon="💸")
st.title("💸 Local Finance Dashboard")
st.markdown("Your private, offline financial tracker.")

# 2. Build the Sidebar Menu
st.sidebar.header("Data Source")
source_option = st.sidebar.radio(
    "Where should we read the data from?",
    ["1. Local SMS Backup (XML)", "2. Local Statement (PDF)", "3. Manual Upload"]
)

password = st.sidebar.text_input("PDF Password (if required)", type="password")

st.sidebar.divider()

# Google Drive Sync Button
if st.sidebar.button("☁️ Fetch Latest from Drive"):
    with st.spinner("Downloading from Google Drive..."):
        success = download_latest_backup("data/raw/sms_backup.xml")
        if success:
            st.sidebar.success("Downloaded! Select Option 1 above to view.")
        else:
            st.sidebar.error("Failed to download.")

# 3. Determine the Target File
raw_data = None
target_file = ""

if source_option == "1. Local SMS Backup (XML)":
    target_file = "data/raw/sms_backup.xml"
    if not os.path.exists(target_file):
        st.warning(f"Could not find {target_file}. Click the Drive button to fetch it, or upload manually.")
        
elif source_option == "2. Local Statement (PDF)":
    target_file = "data/raw/statement.pdf"
    if not os.path.exists(target_file):
        st.warning(f"Could not find {target_file}. Please place it in the data/raw folder.")

elif source_option == "3. Manual Upload":
    uploaded_file = st.sidebar.file_uploader("Upload Bank Statement or SMS Backup", type=['xml', 'pdf'])
    if uploaded_file is not None:
        target_file = os.path.join("data", "raw", uploaded_file.name)
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        with open(target_file, "wb") as f:
            f.write(uploaded_file.getbuffer())

# 4. Process the Data (If a file was found)
if target_file and os.path.exists(target_file):
    with st.spinner("Crunching the numbers..."):
        # Route to the correct parser
        if target_file.endswith('.pdf'):
            raw_data = parse_pdf(target_file, password=password if password else None)
        else:
            raw_data = parse_sms(target_file)

        if raw_data is not None and not raw_data.empty:
            st.success(f"Data extracted successfully from {os.path.basename(target_file)}!")
            summary_data = analyze_monthly_spending(raw_data)
            
            # --- GOOGLE SHEETS UPLOAD BUTTON ---
            if st.button("🚀 Push to Google Sheets", type="primary"):
                with st.spinner("Syncing to cloud..."):
                    push_to_sheets(raw_data, summary_data, "My Finance Tracker")
                    st.toast('Successfully synced to Google Sheets!', icon='🎉')
            
            # ==========================================
            # YEARLY SUMMARY
            # ==========================================
            st.divider()
            st.subheader("📆 Yearly Summary")
            
            if not summary_data.empty:
                yearly_df = summary_data.copy()
                yearly_df['Year'] = yearly_df['Month'].str[:4]
                yearly_totals = yearly_df.groupby('Year')['Total_Spend'].sum().reset_index()
                yearly_totals.rename(columns={'Total_Spend': 'Total Yearly Spend'}, inplace=True)
                yearly_totals.index = yearly_totals.index + 1
                st.dataframe(yearly_totals, use_container_width=True)

            # ==========================================
            # MONTHLY SUMMARYs
            # ==========================================
            st.divider()
            st.subheader("📊 Monthly Summary")
            
            sum_col1, sum_col2, _ = st.columns([1.5, 1.5, 7])
            with sum_col1:
                sum_csv = summary_data.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", data=sum_csv, file_name="monthly_summary.csv", mime="text/csv", key='sum_down')
            with sum_col2:
                show_sum_graph = st.toggle("📈 Show Graph", key='sum_graph')
            
            if show_sum_graph and not summary_data.empty:
                st.bar_chart(summary_data.set_index('Month')['Total_Spend'])
            else:
                # Add this line right here!
                summary_data.index = summary_data.index + 1 
                st.dataframe(summary_data, use_container_width=True)


            # ==========================================
            # RAW TRANSACTIONS
            # ==========================================
            st.divider()
            st.subheader("🔍 Raw Transactions")
            
            raw_col1, raw_col2, _ = st.columns([1.5, 1.5, 7])
            with raw_col1:
                raw_csv = raw_data.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", data=raw_csv, file_name="raw_transactions.csv", mime="text/csv", key='raw_down')
            with raw_col2:
                show_raw_graph = st.toggle("📈 Show Graph", key='raw_graph')
            
            if show_raw_graph:
                graph_df = raw_data.copy()
                graph_df['Date'] = pd.to_datetime(graph_df['Date'], errors='coerce')
                st.scatter_chart(graph_df, x='Date', y='Amount', color='Status')
            else:
                # Add this line right here!
                raw_data.index = raw_data.index + 1 
                
                def color_status(val):
                    color = '#ff4b4b' if val == 'DEBIT' else '#00cc96'
                    return f'color: {color}; font-weight: bold;'
                st.dataframe(raw_data.style.map(color_status, subset=['Status']), use_container_width=True)
            
        else:
            st.error("Could not extract any transactions. Ensure the file format is correct.")