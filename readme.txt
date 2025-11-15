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
7. Right-side trading strategy

Right-Side Trading Strategy:
The right-side trading strategy is a trend-following approach that aims to capture stock momentum by entering positions after a confirmed breakout. This strategy follows the principle of "buy high and sell higher" by identifying stocks that are showing strength and following through on that strength.

Core Components:
1. Price Breakout: Identifies when a stock's price breaks through key resistance levels (previous highs or specified price points)
2. Volume Confirmation: Validates breakouts with significant volume increases to ensure the move has strong backing
3. Technical Indicator Confirmation: Uses the CCI (Commodity Channel Index) indicator to confirm trend direction - specifically looking for CCI to break above a threshold (default -100) from below
4. Moving Average Alignment: Ensures short-term moving averages are above longer-term ones (bullish alignment) to confirm overall trend direction

How It Works:
1. The system scans all tracked stocks daily
2. Evaluates each stock against the right-side trading criteria
3. Adds matching stocks to the watchlist with a recommended action
4. Users can review these opportunities in the Stock View section

Strategy Benefits:
- Reduces risk of trading against the main trend
- Captures stocks with strong momentum
- Filters out false breakouts with volume and technical confirmation
- Helps traders stay on the right side of the market

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