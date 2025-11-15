import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// 股票相关API
export const stockService = {
  getStocks: (params) => api.get(`/stocks`, { params }),
  searchStocks: (keyword) => api.get(`/stocks/search/${keyword}`),
  getStockData: (code) => api.get(`/stocks/${code}`),
  getStockIntegratedData: (code, params) => api.get(`/stocks/${code}/integrated-data`, { params }),
  getStockDetailedInfo: (code) => api.get(`/stocks/${code}/stock-info`),
  triggerDataFetch: () => api.post('/stocks/trigger-fetch'),
  stopDataFetch: () => api.post('/stocks/stop-fetch'), // 添加停止获取数据的API
}

// 技术分析相关API
export const technicalAnalysisService = {
  getStockData: (code, limit, indicators) => api.get(`/technical/${code}`, { params: { limit, indicators } }),
  updateCCI: (code, startDate, endDate) => api.post(`/technical/${code}/update-cci`, { start_date: startDate, end_date: endDate }),
  getIndicators: (stockCode) => api.get('/technical/indicators', { params: { stock_code: stockCode } }),
  getConfiguredIndicators: () => api.get('/technical/config'), // 获取配置的指标列表
  createIndicator: (indicator) => api.post('/technical/config', indicator),
  updateIndicator: (id, indicator) => api.put(`/technical/config`, indicator),
  deleteIndicator: (id) => api.delete(`/technical/config/${id}`),
  updateAllStocksCci: () => api.post('/technical/update-all-cci'),
  updateAllStocksIndicators: () => api.post('/technical/update-all-indicators'),
  recomputeAllStocksIndicators: () => api.post('/technical/recompute-all-indicators'),
}

// 交易记录相关API
export const tradingRecordService = {
  getRecords: (params) => api.get('/trading-records', { params }),
  createRecord: (record) => api.post('/trading-records', record),
  updateRecord: (id, record) => api.put(`/trading-records/${id}`, record),
  deleteRecord: (id) => api.delete(`/trading-records/${id}`),
}

// 交易策略相关API
export const tradingStrategyService = {
  getStrategies: () => api.get('/trading-strategies/strategies'),
  createStrategy: (strategy) => api.post('/trading-strategies/strategies', strategy),
  createRightSideStrategy: (params) => api.post('/trading-strategies/strategies/right_side', params),
  updateStrategy: (id, strategy) => api.put(`/trading-strategies/strategies/${id}`, strategy),
  deleteStrategy: (id) => api.delete(`/trading-strategies/strategies/${id}`),
  executeStrategy: (id) => api.post(`/trading-strategies/evaluate`),
  executeRightSideStrategy: () => api.post(`/trading-strategies/evaluate/right_side`),
}

// 系统配置相关API
export const configurationService = {
  getConfigs: (params) => api.get('/config', { params }),
  createConfig: (config) => api.post('/config', config),
  updateConfig: (config) => api.put('/config', config),
}

// 自选股相关API
export const stockCollectionService = {
  getCollections: () => api.get('/stock-collections'),
  addToCollection: (item) => api.post('/stock-collections', item),
  updateCollection: (id, item) => api.put(`/stock-collections/${id}`, item),
  deleteFromCollection: (id) => api.delete(`/stock-collections/${id}`),
  moveCollection: (id, direction) => api.post(`/stock-collections/${id}/move`, { direction }),
}

export default api