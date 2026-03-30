@echo off
echo ===================================
echo   Starting Local Finance Tracker
echo ===================================
call venv\Scripts\activate

rem Run the command line sync first
python -m src.main

echo.
echo Launching Web Dashboard...
streamlit run app.py

pause