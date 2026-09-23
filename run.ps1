# Greeni5 Plant Nursery Launcher
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "        GREENI5 PLANT NURSERY WEB APPLICATION" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""

Set-Location $PSScriptRoot

if (-not (Test-Path "greeni5.db")) {
    Write-Host "Initializing database..." -ForegroundColor Yellow
    python seed_data.py
}

Write-Host "Starting Greeni5 on http://127.0.0.1:5000 ..." -ForegroundColor Cyan
Write-Host "Admin Portal: http://127.0.0.1:5000/admin" -ForegroundColor Cyan
Write-Host "Admin Login: admin@greeni5.com / Admin@123" -ForegroundColor Gray
Write-Host "Customer Login: customer@greeni5.com / Customer@123" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Yellow

python app.py
