@echo off
REM Monthly Sync Batch File for Windows Task Scheduler
REM Schedule this file to run monthly via Task Scheduler

cd /d "%~dp0.."
echo Starting monthly sync at %date% %time%
echo ==========================================

REM Activate conda if available (adjust path as needed)
call C:\Users\OsterriederJRO\AppData\Local\anaconda3\Scripts\activate.bat

REM Run the sync script
python scripts\20_monthly_sync.py >> logs\monthly_sync.log 2>&1

echo ==========================================
echo Sync completed at %date% %time%
echo Log saved to: logs\monthly_sync.log

REM Optional: Commit and push changes to GitHub
REM git add -A
REM git commit -m "Monthly sync: %date%"
REM git push origin main
