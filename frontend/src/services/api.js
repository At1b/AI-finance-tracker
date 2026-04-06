import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  login: (username, password) => api.post('/login', { username, password }),
  register: (username, password) => api.post('/register', { username, password }),
  
  getTransactions: (username) => api.get(`/transactions?username=${username}`),
  addTransaction: (data, username) => api.post(`/transactions?username=${username}`, data),
  deleteTransaction: (id, username) => api.delete(`/transactions?username=${username}`, { data: { id } }),
  updateTransaction: (data, username) => api.put(`/transactions?username=${username}`, data),
  
  predictCategory: (description) => api.post('/ai/predict-category', { description }),
  getForecast: (username) => api.get(`/ai/forecast?username=${username}`),
  getBudget: (username) => api.get(`/ai/budget?username=${username}`),
  getAlerts: (username) => api.get(`/ai/alerts?username=${username}`),
};
