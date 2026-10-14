$rootDir = Resolve-Path "$PSScriptRoot\.."

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Starting Travelogix Chatbot & Admin Local Development" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\chatbot-backend'; Write-Host 'Chatbot Backend (Port 5052)...' -ForegroundColor Green; python start_dev.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\chatbot'; Write-Host 'Chatbot Frontend (Port 3052)...' -ForegroundColor Green; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\admin-backend'; Write-Host 'Admin Backend (Port 5053)...' -ForegroundColor Green; python start_dev.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\admin'; Write-Host 'Admin Frontend (Port 3053)...' -ForegroundColor Green; npm run dev"

Write-Host "`nAll 4 services launched directly without Docker!" -ForegroundColor Yellow
Write-Host "- Chatbot App     : http://localhost:3052 (API: http://localhost:5052/api/v1/health)" -ForegroundColor Green
Write-Host "- Admin App       : http://localhost:3053 (API: http://localhost:5053/api/v1/health)`n" -ForegroundColor Green
