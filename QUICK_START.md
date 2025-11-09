# Grape Finance - Local Development Setup

## Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB (running locally on port 27017)

## Quick Start

### Option 1: Start everything with one command
```bash
./start_all.sh
```

Or start services individually:
# Terminal 1 - Backend
cd grape-finance/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd grape-finance/frontend
npm install
npm run dev