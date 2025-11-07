import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import AppLayout from './components/Layout';
import Stocks from './pages/Stocks';
import TechnicalAnalysis from './pages/TechnicalAnalysis';
import TradingStrategies from './pages/TradingStrategies';
import StockCollections from './pages/StockCollections';
import TradingRecords from './pages/TradingRecords';
import Configuration from './pages/Configuration';
import './App.css';

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <AppLayout>
          <Routes>
            <Route path="/" element={<Stocks />} />
            <Route path="/stocks" element={<Stocks />} />
            <Route path="/technical" element={<TechnicalAnalysis />} />
            <Route path="/strategies" element={<TradingStrategies />} />
            <Route path="/collections" element={<StockCollections />} />
            <Route path="/records" element={<TradingRecords />} />
            <Route path="/config" element={<Configuration />} />
          </Routes>
        </AppLayout>
      </Router>
    </ConfigProvider>
  );
};

export default App;
