Grape Finance - Stock Analysis System

Project Structure:
- Backend: FastAPI with MongoDB, BaoStock integration
- Frontend: React with TradingView charts
- Database: MongoDB for data storage

Key Features:
1. Automated stock data fetching from BaoStock
2. Configurable technical analysis (CCI with dynamic parameters)
3. Trading strategy configuration and backtesting
4. Stock collection management
5. Real-time monitoring and income calculation
6. Comprehensive configuration management

Setup Instructions:

1. Backend Setup:
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload

2. Frontend Setup:
   cd frontend
   npm install
   npm start

3. Docker Setup:
   docker-compose up -d

4. Access Points:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Frontend: http://localhost:3000

Configuration:
- Modify system settings through /api/config endpoints
- Set up trading strategies through UI
- Configure technical analysis parameters

Data Flow:
1. System fetches stock list on startup
2. Daily data fetched automatically or manually
3. Technical indicators calculated automatically
4. Trading strategies evaluated against indicators
5. Results stored in collections for monitoring

Note: Make sure to have stable internet connection for BaoStock API calls.
