import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const stockAPI = {
  getStocks: (params?: any) => api.get('/stocks', { params }),
  getStockDailyData: (code: string, params?: any) => 
    api.get(`/stocks/${code}/daily`, { params }),
  triggerDataFetch: () => api.post('/stocks/trigger-fetch'),
};

export const technicalAPI = {
  getIndicators: (code: string, indicatorType: string, params?: any) =>
    api.get('/technical/indicators', { 
      params: { stock_code: code, indicator_type: indicatorType, ...params } 
    }),
  createConfig: (config: any) => api.post('/technical/config', config),
};

export const tradingAPI = {
  getStrategies: () => api.get('/trading/strategies'),
  createStrategy: (strategy: any) => api.post('/trading/strategies', strategy),
  updateStrategy: (id: string, strategy: any) => api.put(`/trading/strategies/${id}`, strategy),
  deleteStrategy: (id: string) => api.delete(`/trading/strategies/${id}`),
  evaluateStrategies: () => api.post('/trading/evaluate'),
};

export const collectionAPI = {
  getCollections: (params?: any) => api.get('/collections', { params }),
  addToCollection: (item: any) => api.post('/collections', item),
  removeFromCollection: (id: string) => api.delete(`/collections/${id}`),
  updateCollection: (id: string, updates: any) => api.put(`/collections/${id}`, updates),
};

export const configAPI = {
  getConfigs: (params?: any) => api.get('/config', { params }),
  updateConfig: (config: any) => api.put('/config', config),
};

export const tradingRecordAPI = {
  getRecords: (params?: any) => api.get('/trading-records', { params }),
  createRecord: (record: any) => api.post('/trading-records', record),
  updateRecord: (id: string, record: any) => api.put(`/trading-records/${id}`, record),
  deleteRecord: (id: string) => api.delete(`/trading-records/${id}`),
};

export default api;
