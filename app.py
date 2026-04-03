import streamlit as st
import pandas as pd
import os
from src.parser import parse_sms, parse_pdf
from src.analyzer import analyze_monthly_spending
from src.drive_api import download_latest_backup
from src.sheets_api import push_to_sheets

# --- 1. Setup the Page ---
st.set_page_config(page_title="My Finance Tracker", layout="wide", page_icon="💸")

# --- 2. Initialize Session State ---
# This helps the app remember if we should show the "Menu" or the "Dashboard"
if 'data_processed' not in st.session_state:
    st.session_state.data_processed = False
if 'raw_data' not in st.session_state:
    st.session_state.raw_data = None

# --- Header ---
st.title("💸 Local Finance Dashboard")
st.markdown("_Your private, automated financial command center._")
st.divider()

# ==========================================
# VIEW 1: THE "WHICH WAY" LANDING PAGE
# ==========================================
if not st.session_state.data_processed:
    st.subheader("Step 1: Select Your Data Source")
    
    # We put the options in columns to make it look like a nice menu
    col1, col2 = st.columns([2, 1])
    
    with col1:
        source_option = st.radio(
            "How would you like to load your transactions?",
            ["1. Local SMS Backup (XML)", "2. Local Statement (PDF)", "3. Manual Upload"]
        )
        password = st.text_input("PDF Password (if encrypted)", type="password")
    
    with col2:
        st.info("☁️ **Google Drive Sync**\n\nFetch your latest SMS backup automatically.")
        if st.button("Fetch Latest from Drive", use_container_width=True):
            with st.spinner("Accessing Google Drive..."):
                os.makedirs("data/raw", exist_ok=True)
                success = download_latest_backup("data/raw/sms_backup.xml")
                if success:
                    st.success("Sync Complete! Select 'Local SMS Backup' to proceed.")
                else:
                    st.error("Drive Sync Failed. Check your API credentials.")

    st.divider()
    
    # Target file logic
    target_file = ""
    if source_option == "1. Local SMS Backup (XML)":
        target_file = "data/raw/sms_backup.xml"
    elif source_option == "2. Local Statement (PDF)":
        target_file = "data/raw/statement.pdf"
    elif source_option == "3. Manual Upload":
        uploaded_file = st.file_uploader("Upload File", type=['xml', 'pdf'])
        if uploaded_file:
            target_file = os.path.join("data", "raw", uploaded_file.name)
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            with open(target_file, "wb") as f:
                f.write(uploaded_file.getbuffer())

    # The "Analyze" Button (Moves us to View 2)
    if target_file and os.path.exists(target_file):
        if st.button("🚀 Analyze Data", type="primary", use_container_width=True):
            with st.spinner("Crunching the numbers..."):
                if target_file.lower().endswith('.pdf'):
                    st.session_state.raw_data = parse_pdf(target_file, password=password if password else None)
                else:
                    st.session_state.raw_data = parse_sms(target_file)
                
                if st.session_state.raw_data is not None and not st.session_state.raw_data.empty:
                    st.session_state.data_processed = True
                    st.rerun() # This instantly refreshes the page to show View 2
                else:
                    st.error("Extraction failed. Check file formatting or PDF password.")
    elif source_option != "3. Manual Upload":
         st.warning("⚠️ File not found. Please ensure it is in the `data/raw/` folder or click Fetch from Drive.")


# ==========================================
# VIEW 2: THE RESULTS DASHBOARD
# ==========================================
if st.session_state.data_processed and st.session_state.raw_data is not None:
    
    # A button to let the user go back to the start menu
    if st.button("← Go Back / Load Different File"):
        st.session_state.data_processed = False
        st.session_state.raw_data = None
        st.rerun()
        
    summary_data = analyze_monthly_spending(st.session_state.raw_data)

    # --- API Action: Push to Sheets ---
    if st.button("🚀 Sync to Google Sheets", type="primary"):
        with st.spinner("Updating your Spreadsheet..."):
            push_to_sheets(st.session_state.raw_data, summary_data, "My Finance Tracker")
            st.toast('Google Sheets Updated!', icon='🎉')

    # --- UI: Yearly Summary ---
    st.divider()
    st.subheader("📆 Yearly Overview")
    yearly_df = summary_data.copy()
    yearly_df['Year'] = yearly_df['Month'].str[:4]
    
    # Group by Year and sum BOTH Spend and Credit
    yearly_totals = yearly_df.groupby('Year')[['Total Spend', 'Total Credit']].sum().reset_index()
    yearly_totals.index = yearly_totals.index + 1
    st.dataframe(yearly_totals, use_container_width=True)

    # --- UI: Monthly Summary ---
    st.divider()
    st.subheader("📊 Monthly Trends")
    col_a, col_b, _ = st.columns([1.5, 1.5, 7])
    with col_a:
        csv_sum = summary_data.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export CSV", data=csv_sum, file_name="monthly_summary.csv")
    with col_b:
        show_graph = st.toggle("📈 Show Chart")

    if show_graph:
        # stack=False places them side-by-side. 
        # color maps Red to Spend and Green to Credit.
        st.bar_chart(
            summary_data.set_index('Month')[['Total Spend', 'Total Credit']],
            color=["#ff4b4b", "#00cc96"], 
            stack=False 
        )
    else:
        summary_data.index = summary_data.index + 1
        st.dataframe(summary_data, use_container_width=True)
        
    # --- UI: Raw Transactions ---
    st.divider()
    st.subheader("🔍 Transaction Ledger")
    raw_col1, raw_col2, _ = st.columns([1.5, 1.5, 7])
    with raw_col1:
        csv_raw = st.session_state.raw_data.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Raw", data=csv_raw, file_name="raw_data.csv")
    with raw_col2:
        show_raw_graph = st.toggle("📈 Data Points")

    if show_raw_graph:
        viz_df = st.session_state.raw_data.copy()
        viz_df['Date'] = pd.to_datetime(viz_df['Date'], errors='coerce')
        
        # Split into two columns: Income (Positive) and Expense (Negative)
        viz_df['Expense'] = viz_df.apply(lambda x: -x['Amount'] if x['Status'] == 'DEBIT' else 0, axis=1)
        viz_df['Income'] = viz_df.apply(lambda x: x['Amount'] if x['Status'] == 'CREDIT' else 0, axis=1)
        
        # Plot them as a time-series bar chart
        st.bar_chart(
            viz_df.set_index('Date')[['Expense', 'Income']],
            color=["#ff4b4b", "#00cc96"]
        )
    else:
        st.session_state.raw_data.index = st.session_state.raw_data.index + 1
        def color_status(val):
            color = '#ff4b4b' if val == 'DEBIT' else '#00cc96'
            return f'color: {color}; font-weight: bold;'
        st.dataframe(st.session_state.raw_data.style.map(color_status, subset=['Status']), use_container_width=True)