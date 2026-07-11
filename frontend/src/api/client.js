import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60000, // 60s — ML inference can be slow on first load
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor — attach Bearer token ─────────────────
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ── Response interceptor — handle 401 globally ────────────────
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      // Redirect to login (without React Router dependency)
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ── API helpers ────────────────────────────────────────────────
export const authAPI = {
  register: (data) => client.post('/api/auth/register', data),
  login: (data) => client.post('/api/auth/login', data),
  me: () => client.get('/api/auth/me'),
}

export const predictAPI = {
  predict: (formData) =>
    client.post('/api/predict', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  getById: (id) => client.get(`/api/predict/${id}`),
}

export const historyAPI = {
  getHistory: (page = 1, pageSize = 20) =>
    client.get('/api/history', { params: { page, page_size: pageSize } }),
  deleteRecord: (id) => client.delete(`/api/history/${id}`),
}

export default client
