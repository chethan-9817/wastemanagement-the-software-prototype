@echo off
echo ==============================================
echo Starting Municipal Waste Management Dashboard...
echo ==============================================
cd /d "%~dp0"

echo Checking and installing requirements...
pip install -r requirements.txt > nul 2>&1

echo Launching Dashboard...
echo A new browser window will open shortly.
streamlit run app.py

pause
