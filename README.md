# 📊 Personal Finance Dashboard

A comprehensive, interactive web dashboard built with Python and Streamlit that tracks, analyzes, and visualizes personal financial transactions extracted from SMS backups.

## ✨ Features & Data Processing

This project automates the workflow of tracking expenses by turning raw SMS data into a clean, readable financial dashboard.

* **Data Extraction:** Parses raw XML SMS backup files to identify and extract bank transaction messages.
* **Intelligent Processing:** Uses `pandas` to clean data, parse dates, and categorize transactions as `DEBIT` or `CREDIT`.
* **Dynamic Aggregations:** Automatically calculates and groups spending into **Daily, Weekly, Monthly, and Yearly** summaries.
* **Interactive UI:** Built with Streamlit, featuring interactive toggles to switch between tabular data and visual charts (Bar charts and Scatter plots).
* **Visual Enhancements:** * Custom pandas styling color-codes DEBITs (red) and CREDITs (green) for instant readability.
  * User-friendly 1-based indexing on all data tables.
* **Export Functionality:** Includes built-in buttons to download processed summaries and raw transaction data as clean `.csv` files.

## 🚀 Steps to Implement (Local Setup)

Follow these steps to run the dashboard on your local machine.

### 1. Prerequisites
Ensure you have Python installed on your system. You will also need `pip` to install the required libraries.

### 2. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME


# Local Finance Tracker
A privacy-first Python application that parses local bank SMS exports, 
analyzes spending habits, and synchronizes data with Google Sheets.

## Setup
1. Activate venv: `venv\Scripts\activate`
2. Install deps: `pip install -r requirements.txt`
3. Place SMS data in `data/raw/`
4. Run: `python src/main.py`
