import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
};

// Statements API
export const statementsAPI = {
  list: () => api.get('/statements'),
  get: (id) => api.get(`/statements/${id}`),
  upload: (formData) => api.post('/statements/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  parse: (id) => api.post(`/statements/${id}/parse`),
  recategorize: (id) => api.post(`/statements/${id}/recategorize`),
  delete: (id) => api.delete(`/statements/${id}`),
};

// Transactions API
export const transactionsAPI = {
  list: (params) => api.get('/transactions', { params }),
  get: (id) => api.get(`/transactions/${id}`),
  update: (id, data, createRule = false) =>
    api.patch(`/transactions/${id}?create_rule=${createRule}`, data),
  bulkUpdate: (transaction_ids, category_id) =>
    api.post('/transactions/bulk-update', { transaction_ids, category_id }),
};

// Categories API
export const categoriesAPI = {
  list: () => api.get('/categories'),
  get: (id) => api.get(`/categories/${id}`),
  create: (data) => api.post('/categories', data),
  delete: (id) => api.delete(`/categories/${id}`),
};

// Merchant Rules API
export const merchantRulesAPI = {
  list: () => api.get('/merchant-rules'),
  create: (data) => api.post('/merchant-rules', data),
  delete: (id) => api.delete(`/merchant-rules/${id}`),
};

// Analytics API
export const analyticsAPI = {
  getSummary: (params) => api.get('/analytics/summary', { params }),
  getSpendingByCategory: (params) => api.get('/analytics/spending/by-category', { params }),
  getSpendingTimeSeries: (params) => api.get('/analytics/spending/time-series', { params }),
  getTopMerchants: (params) => api.get('/analytics/top-merchants', { params }),
  exportCSV: (params) => api.get('/analytics/export/csv', { params, responseType: 'blob' }),
};

export default api;
