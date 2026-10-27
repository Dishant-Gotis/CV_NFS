# VelocityCV Launcher
Set-Location $PSScriptRoot
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Launching VelocityCV (Classic 90s Arcade Edition)" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" main.py @args
