@echo off
echo Starting Grape Finance Frontend...

REM Navigate to frontend directory
cd frontend

REM Install dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

REM Start the development server
echo Starting React development server...
npm run dev

pause