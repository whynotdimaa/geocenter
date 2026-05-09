import { create } from 'zustand'
import api from '../api/axios'

const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  loading: false,
  error: null,

  // Логін
  login: async (email, password) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.post('/auth/login', { email, password })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ isAuthenticated: true, loading: false })
      // Одразу підтягуємо дані юзера
      await useAuthStore.getState().fetchMe()
    } catch (err) {
      set({
        error: err.response?.data?.detail || 'Невірний email або пароль',
        loading: false,
      })
    }
  },

  // Реєстрація
  register: async (username, email, password, password2) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.post('/auth/register', { username, email, password, password2 })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ isAuthenticated: true, loading: false })
      await useAuthStore.getState().fetchMe()
    } catch (err) {
      const detail = err.response?.data?.detail
      let msg = 'Помилка реєстрації'
      if (Array.isArray(detail)) {
        msg = detail.map(e => e.msg).join(', ')
      } else if (typeof detail === 'string') {
        msg = detail
      }
      set({ error: msg, loading: false })
    }
  },

  // Логаут
  logout: async () => {
    const refresh = localStorage.getItem('refresh_token')
    try {
      if (refresh) await api.post('/auth/logout', { refresh_token: refresh })
    } catch {}
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
  },

  // Поточний юзер
  fetchMe: async () => {
    try {
      const { data } = await api.get('/users/me')
      set({ user: data, isAuthenticated: true })
    } catch {
      set({ user: null, isAuthenticated: false })
    }
  },

  clearError: () => set({ error: null }),
}))

export default useAuthStore
