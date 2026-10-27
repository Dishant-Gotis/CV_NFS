@echo off
cd /d "%~dp0"
echo ========================================================
echo  Launching VelocityCV (Classic 90s Arcade Edition)
echo ========================================================
.\.venv\Scripts\python.exe main.py %*
pause
