@echo off
echo Starting Grape Finance Application...

REM Start backend in a new window
start "Grape Finance Backend" cmd /k "cd /d %~dp0 && call start_backend.bat"

REM Wait for backend to start
timeout /t 5

REM Start frontend in a new window
start "Grape Finance Frontend" cmd /k "cd /d %~dp0 && call start_frontend.bat"

echo.
echo Backend will be running on: http://localhost:8000
echo Frontend will be running on: http://localhost:3000
echo API documentation: http://localhost:8000/docs
echo.
echo Both windows have been opened. Close them manually when done.
echo.
pause