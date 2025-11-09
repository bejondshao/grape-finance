@echo off
echo Starting Grape Finance Backend...

REM Navigate to backend directory
cd backend

REM Check if .env file exists
if not exist .env (
    echo Warning: .env file not found. Using default settings.
)

REM Check if virtual environment exists, if not create it
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Start the application
echo Starting FastAPI server...
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause