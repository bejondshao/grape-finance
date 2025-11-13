import React from 'react'
import { Routes, Route } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import Dashboard from './pages/Dashboard'
import StockList from './pages/StockList'
import StockCollection from './pages/StockCollection'
import TechnicalAnalysis from './pages/TechnicalAnalysis'
import TradingStrategy from './pages/TradingStrategy'
import TradingRecords from './pages/TradingRecords'
import Configuration from './pages/Configuration'
import DataFetch from './pages/DataFetch'
import StockView from './pages/StockView'

function App() {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/stocks" element={<StockList />} />
        <Route path="/collection" element={<StockCollection />} />
        <Route path="/technical-analysis" element={<TechnicalAnalysis />} />
        <Route path="/trading-strategy" element={<TradingStrategy />} />
        <Route path="/trading-records" element={<TradingRecords />} />
        <Route path="/configuration" element={<Configuration />} />
        <Route path="/data-fetch" element={<DataFetch />} />
        <Route path="/stock-view" element={<StockView />} />
      </Routes>
    </MainLayout>
  )
}

export default App
