@echo off
chcp 65001 >nul
echo ============================================
echo 太极OS Dashboard v4.0
echo ============================================
echo.
echo 启动服务器...
cd /d "%~dp0"
"C:\Program Files\Python312\python.exe" server.py
pause
