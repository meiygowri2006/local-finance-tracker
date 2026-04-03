# 💸 Local Finance Tracker

A privacy-focused, offline-first personal finance dashboard built with Python and Streamlit. This tool automates the extraction of financial transactions from Android SMS XML backups and Bank Statement PDFs, categorizes them, and provides a beautiful interactive dashboard to visualize your spending habits.

## ✨ Features
* **Dual Data Sources:** Parses both Android SMS Backup (`.xml`) and Bank Statements (`.pdf`).
* **Privacy First:** All data is processed completely locally on your machine.
* **Smart Extraction:** Uses PyMuPDF and Regex to accurately pull `Date`, `Description`, `Amount`, and `Status` (Debit/Credit).
* **Interactive Dashboard:** Built with Streamlit, featuring yearly overviews, monthly trends, and raw transaction ledgers.
* **Cloud Sync:** Pulls latest SMS backups from Google Drive and pushes processed financial summaries to Google Sheets.

## 🛠️ Prerequisites
Before running this project, ensure you have the following installed:
1. Python 3.9 or higher.
2. Google Cloud API Credentials (for Drive and Sheets sync). 

## 🚀 Installation & Setup

**1. Clone the repository**
```bash
git clone [https://github.com/meiygowri2006/local-finance-tracker.git](https://github.com/meiygowri2006/local-finance-tracker.git)
cd local-finance-tracker