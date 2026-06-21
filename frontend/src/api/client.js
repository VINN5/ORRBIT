import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request automatically
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('orrbit_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle expired/invalid tokens globally
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('orrbit_token')
      localStorage.removeItem('orrbit_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ── Auth API ──────────────────────────────────────────────────────────────────

export async function registerUser(email, username, password) {
  const { data } = await client.post('/auth/register', { email, username, password })
  return data
}

export async function loginUser(email, password) {
  const { data } = await client.post('/auth/login', { email, password })
  return data
}

export async function getCurrentUser() {
  const { data } = await client.get('/auth/me')
  return data
}

export async function logoutUser() {
  const { data } = await client.post('/auth/logout')
  return data
}

// ── Chat API ───────────────────────────────────────────────────────────────────

export async function sendMessage(message, sessionId = 'default') {
  const { data } = await client.post('/chat', { message, session_id: sessionId })
  return data
}

export default client