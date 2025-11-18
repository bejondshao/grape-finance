import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8000/api'

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 将超时时间从10秒增加到30秒
})

// 添加响应拦截器来统一处理响应数据
api.interceptors.response.use(
  (response) => {
    // 保持响应结构，但需要处理数组响应
    // 如果返回的是数组，包装成 {data: array} 格式
    if (Array.isArray(response.data)) {
      return {
        data: response.data
      };
    }
    // 如果返回的是对象，直接返回
    return response.data;
  },
  (error) => {
    console.error('API Error:', error.response || error.message);
    // 确保错误对象包含响应数据
    if (error.response && error.response.data) {
      // 将响应数据附加到错误对象上，以便组件可以访问
      error.errorMessage = error.response.data.detail || error.response.data.message || 'Unknown error';
    }
    return Promise.reject(error);
  }
);

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
  createStrongKStrategy: (params) => api.post('/trading-strategies/strategies/strong_k', params),
  createBottomReversalStrategy: (params) => api.post('/trading-strategies/strategies/bottom_reversal', params),
  updateStrategy: (id, strategy) => api.put(`/trading-strategies/strategies/${id}`, strategy),
  deleteStrategy: (id) => api.delete(`/trading-strategies/strategies/${id}`),
  executeStrategy: (id) => api.post(`/trading-strategies/evaluate`),
  executeRightSideStrategy: () => api.post(`/trading-strategies/evaluate/right_side`),
  manualExecuteStrategy: (params) => api.post('/trading-strategies/execute/manual', params),
  stopStrategyExecution: () => api.post('/trading-strategies/execute/stop'), // 添加停止策略执行的API
  filterStocks: (params) => api.get('/trading-strategies/stocks/filter', { params }),
  getExecutionStatus: (executionId) => api.get(`/trading-strategies/execute/status/${executionId}`), // 添加获取执行状态的API
}

// 系统配置相关API
export const configurationService = {
  getConfigs: (params) => api.get('/config', { params }),
  createConfig: (config) => api.post('/config', config),
  updateConfig: (config) => api.put('/config', config),
}

// 自选股相关API
export const stockCollectionService = {
  getCollections: () => api.get('/collections'),
  addToCollection: (item) => api.post('/collections', item),
  updateCollection: (id, item) => api.put(`/collections/${id}`, item),
  deleteFromCollection: (id) => api.delete(`/collections/${id}`),
  clearAllCollections: () => api.delete('/collections'), // 添加清空所有收藏的API
  moveCollection: (id, direction) => api.post(`/collections/${id}/move`, { direction }),
}

export default api