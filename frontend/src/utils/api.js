import axios from 'axios'
import { auth } from '../firebase/config'

const api = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL,
})

// Attach Firebase token to every request
api.interceptors.request.use(async (config) => {
  const user = auth.currentUser
  if (user) {
    const token = await user.getIdToken()
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Global 403 handler — caller can listen for FREE_LIMIT_REACHED
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response?.status === 403 &&
      error.response?.data?.detail === 'FREE_LIMIT_REACHED'
    ) {
      window.dispatchEvent(new CustomEvent('free-limit-reached'))
    }
    return Promise.reject(error)
  }
)

export default api
