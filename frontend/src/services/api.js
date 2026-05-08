import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (email, password) => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    return api.post('/auth/login', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  verifyEmail: (email, code) => api.post('/auth/verify-email', { email, code }),
  resendOtp: (email) => api.post('/auth/resend-otp', { email, code: '' }),
  forgotPassword: (email) => api.post('/auth/forgot-password', { email, code: '' }),
  resetPassword: (email, code, new_password) => api.post('/auth/reset-password', { email, code, new_password }),
}

export const userApi = {
  getMe: () => api.get('/users/me'),
  updateMe: (data) => api.put('/users/me', data),
}

export const cvApi = {
  upload: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/cv/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  download: () => api.get('/cv/download', { responseType: 'blob' }),
  analyze: () => api.post('/cv/analyze'),
}

export const jobsApi = {
  list: (params) => api.get('/jobs/', { params }),
  getById: (id) => api.get(`/jobs/${id}`),
  recommended: () => api.get('/jobs/recommended'),
  scrape: (keywords, location, company = '') => api.post('/jobs/scrape', null, { params: { keywords, location, company } }),
}

export const applicationsApi = {
  list: () => api.get('/applications/'),
  create: (data) => api.post('/applications/', data),
  update: (id, data) => api.put(`/applications/${id}`, data),
  delete: (id) => api.delete(`/applications/${id}`),
  generateLetter: (id) => api.post(`/applications/${id}/cover-letter`),
  generateEmail: (id) => api.post(`/applications/${id}/email`),
}

export const statsApi = {
  get: () => api.get('/stats/'),
  notifications: () => api.get('/stats/notifications'),
  markRead: (id) => api.post(`/stats/notifications/${id}/read`),
}

export const automationApi = {
  getLatestReport: () => api.get('/automation/report/latest'),
  getHistory: () => api.get('/automation/report/history'),
  runNow: () => api.post('/automation/run'),
  getDrafts: () => api.get('/automation/drafts'),
  validateDraft: (id) => api.post(`/automation/drafts/${id}/validate`),
  discardDraft: (id) => api.delete(`/automation/drafts/${id}`),
}

export default api
