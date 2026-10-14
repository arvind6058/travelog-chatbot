@echo off
echo ============================================================
echo  Starting Travelogix Chatbot ^& Dashboard Local Development
echo ============================================================
echo.

echo Launching Chatbot Backend (Port 5052)...
start "Chatbot Backend (Port 5052)" cmd /k "cd /d %~dp0chatbot-backend && python start_dev.py"

echo Launching Chatbot Web (Port 3052)...
start "Chatbot Web (Port 3052)" cmd /k "cd /d %~dp0chatbot && npm run dev"

echo Launching Chatbot Dashboard Backend (Port 5053)...
start "Chatbot Dashboard Backend (Port 5053)" cmd /k "cd /d %~dp0admin-backend && python start_dev.py"

echo Launching Chatbot Dashboard Web (Port 3053)...
start "Chatbot Dashboard Web (Port 3053)" cmd /k "cd /d %~dp0admin && npm run dev"

echo.
echo All 4 services are starting in separate terminal windows!
echo - Chatbot: http://localhost:3052 (API: 5052)
echo - Chatbot Dashboard: http://localhost:3053 (API: 5053)
echo.
