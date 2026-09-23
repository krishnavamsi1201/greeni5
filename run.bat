@echo off
title Greeni5 Plant Nursery Web Server
color 0A
cd /d "%~dp0"

echo ==========================================================
echo        GREENI5 PLANT NURSERY WEB APPLICATION
echo ==========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python is not found in your Windows PATH!
    echo Please install Python from https://www.python.org/ or Microsoft Store.
    echo.
    pause
    exit /b
)

echo [1/3] Checking dependencies...
python -m pip install -r requirements.txt >nul 2>nul

echo [2/3] Checking database...
if not exist "greeni5.db" (
    echo Seeding greeni5 database with sample plants...
    python seed_data.py
)

echo [3/3] Starting server and launching browser...
echo.
echo ==========================================================
echo  Website URL : http://127.0.0.1:5000
echo  Admin URL   : http://127.0.0.1:5000/admin
echo.
echo  Demo Logins:
echo   - Admin:    admin@greeni5.com    / Admin@123
echo   - Customer: customer@greeni5.com / Customer@123
echo ==========================================================
echo.
echo [NOTE] Keep this window OPEN while using the website!
echo (Press Ctrl+C to stop)
echo.

python app.py

if %errorlevel% neq 0 (
    echo.
    echo Server exited with an error.
    pause
)
