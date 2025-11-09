# Grape Finance - Windows Setup

## Prerequisites
- Python 3.11+ (add to PATH during installation)
- Node.js 18+ 
- MongoDB Community Edition

## Installation Steps

### 1. Install MongoDB
- Download from https://www.mongodb.com/try/download/community
- Run installer, choose "Complete" setup
- Check "Install MongoDB as a Service"
- MongoDB will run automatically on startup

### 2. Clone/Download the Project
- Extract the grape-finance project to a folder like `C:\grape-finance`

### 3. Quick Start
Double-click `start_all.bat` - this will:
- Open two command windows
- Set up Python virtual environment
- Install dependencies
- Start both backend and frontend

### 4. Manual Start (Alternative)
- Double-click `start_backend.bat` (starts backend on port 8000)
- Double-click `start_frontend.bat` (starts frontend on port 3000)

## Access Points
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Troubleshooting

### MongoDB Connection Issues
1. Open Services (Windows Key + R, type `services.msc`)
2. Find "MongoDB" service
3. Ensure it's running, if not right-click and Start

### Python Not Found
1. Reinstall Python and check "Add Python to PATH"
2. Or manually add Python to PATH environment variable

### Node.js Not Found
1. Reinstall Node.js
2. Restart command prompt after installation

### Port Already in Use
- Change ports in `.env` (backend) and `vite.config.ts` (frontend)
- Or stop other applications using ports 3000/8000

=====================

Running on Windows
Easy Method:

    Double-click start_all.bat

    Wait for both windows to open

    Access http://localhost:3000

Manual Method:

    Double-click start_backend.bat (wait for it to fully start)

    Double-click start_frontend.bat

    Access http://localhost:3000

Command Line Method:
cmd

# Backend

```
cd grape-finance\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

# Frontend (new command prompt)
```
cd grape-finance\frontend
npm install
npm run dev
```

Windows-Specific Notes

* MongoDB: Install as a service for automatic startup
* Python: Make sure it's added to PATH during installation
* Node.js: The installer should add it to PATH automatically
* Firewall: You may need to allow Python and Node.js through Windows Firewall on first run

The batch files will handle all the setup automatically. Just make sure MongoDB is installed and running, then double-click start_all.bat!