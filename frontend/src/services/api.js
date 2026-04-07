import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  login: (username, password) => api.post('/login', { username, password }),
  register: (username, password, job, base_income) => api.post('/register', { username, password, job, base_income }),
  getProfile: (username) => api.get(`/user/profile?username=${username}`),
  updateProfile: (username, data) => api.put(`/user/profile?username=${username}`, data),
  
  getTransactions: (username) => api.get(`/transactions?username=${username}`),
  addTransaction: (data, username) => api.post(`/transactions?username=${username}`, data),
  deleteTransaction: (id, username) => api.delete(`/transactions?username=${username}`, { data: { id } }),
  updateTransaction: (data, username) => api.put(`/transactions?username=${username}`, data),
  
  predictCategory: (description) => api.post('/ai/predict-category', { description }),
  getForecast: (username) => api.get(`/ai/forecast?username=${username}`),
  getBudget: (username, month = null) => api.get(`/ai/budget?username=${username}${month ? `&month=${month}` : ''}`),
  getAlerts: (username) => api.get(`/ai/alerts?username=${username}`),
};
