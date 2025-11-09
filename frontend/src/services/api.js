import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const stockService = {
  getStocks: (params) => api.get('/stocks', { params }),
  getStockHistory: (code, params) => api.get(`/stocks/${code}/daily`, { params }),
  triggerFetch: () => api.post('/stocks/trigger-fetch'),
  getFetchProgress: () => api.get('/stocks/fetch-progress'),
}

export const technicalAnalysisService = {
  getIndicators: () => api.get('/technical-analysis'),
  createIndicator: (data) => api.post('/technical-analysis', data),
  updateIndicator: (id, data) => api.put(`/technical-analysis/${id}`, data),
  deleteIndicator: (id) => api.delete(`/technical-analysis/${id}`),
  calculateCCI: (code, params) => api.get(`/technical-analysis/${code}/cci`, { params }),
}

export const tradingStrategyService = {
  getStrategies: () => api.get('/trading-strategies'),
  createStrategy: (data) => api.post('/trading-strategies', data),
  updateStrategy: (id, data) => api.put(`/trading-strategies/${id}`, data),
  deleteStrategy: (id) => api.delete(`/trading-strategies/${id}`),
  executeStrategy: (strategyId) => api.post(`/trading-strategies/${strategyId}/execute`),
}

export const stockCollectionService = {
  getCollection: (params) => api.get('/stock-collection', { params }),
  addToCollection: (data) => api.post('/stock-collection', data),
  updateCollection: (id, data) => api.put(`/stock-collection/${id}`, data),
  removeFromCollection: (id) => api.delete(`/stock-collection/${id}`),
}

export const tradingRecordService = {
  getRecords: (params) => api.get('/trading-records', { params }),
  createRecord: (data) => api.post('/trading-records', data),
  updateRecord: (id, data) => api.put(`/trading-records/${id}`, data),
  deleteRecord: (id) => api.delete(`/trading-records/${id}`),
  calculateProfit: (params) => api.get('/trading-records/profit', { params }),
}

export const configurationService = {
  getConfigs: (params) => api.get('/configurations', { params }),
  updateConfig: (key, data) => api.put(`/configurations/${key}`, data),
  createConfig: (data) => api.post('/configurations', data),
}

export default api
