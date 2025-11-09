GRAPE FINANCE FRONTEND SETUP GUIDE

1. PREREQUISITES
   - Node.js (version 16 or higher)
   - npm (version 7 or higher)

2. PROJECT SETUP

   Option A: Using Python script
   -----------------------------
   python create_grape_finance_frontend.py
   cd grape-finance-frontend
   npm install
   npm run dev

   Option B: Manual setup
   ----------------------
   mkdir grape-finance-frontend
   cd grape-finance-frontend
   Copy all the provided files to their respective directories
   npm install
   npm run dev

3. PROJECT STRUCTURE
   src/
   ├── components/
   │   └── layout/
   │       └── MainLayout.jsx
   ├── pages/
   │   ├── Dashboard.jsx
   │   ├── StockList.jsx
   │   ├── StockCollection.jsx
   │   ├── TechnicalAnalysis.jsx
   │   ├── TradingStrategy.jsx
   │   ├── TradingRecords.jsx
   │   ├── DataFetch.jsx
   │   └── Configuration.jsx
   ├── services/
   │   └── api.js
   ├── utils/
   │   └── helpers.js
   ├── types/
   │   └── index.js
   ├── App.jsx
   ├── main.jsx
   └── index.css

4. FEATURES IMPLEMENTED

   ✅ Main Layout with Navigation
   ✅ Stock List with Filters and Search
   ✅ Stock Collection Management
   ✅ Technical Analysis Configuration
   ✅ Trading Strategy Configuration
   ✅ Trading Records with Profit Calculation
   ✅ Data Fetch Management with Progress Tracking
   ✅ System Configuration Management
   ✅ Responsive Design with Ant Design
   ✅ Real-time Data Updates
   ✅ Comprehensive Error Handling

5. BACKEND INTEGRATION

   The frontend expects the backend to be running on http://localhost:8000
   API endpoints are configured in src/services/api.js

6. KEY FUNCTIONALITIES

   - Real-time stock data display
   - Configurable technical indicators
   - Dynamic trading strategy creation
   - Profit tracking and calculation
   - Data synchronization management
   - System configuration through UI

7. DEVELOPMENT

   Start development server: npm run dev
   Build for production: npm run build
   Preview production build: npm run preview

8. NOTES

   - Ensure backend services are running before starting frontend
   - Proxy configuration in vite.config.js handles CORS
   - All API calls are centralized in services/api.js
   - Components are modular and reusable
   - Error handling and loading states implemented throughout

For any issues, check the browser console for error messages and ensure all environment requirements are met.
