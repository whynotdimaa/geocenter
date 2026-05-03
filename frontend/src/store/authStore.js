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
      const { data } = await api.post('/auth/login/', { email, password })
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
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
      await api.post('/auth/register/', { username, email, password, password2 })
      // Після реєстрації одразу логінимось
      await useAuthStore.getState().login(email, password)
    } catch (err) {
      const errors = err.response?.data
      const msg = errors
        ? Object.values(errors).flat().join(' ')
        : 'Помилка реєстрації'
      set({ error: msg, loading: false })
    }
  },

  // Логаут
  logout: async () => {
    const refresh = localStorage.getItem('refresh_token')
    try {
      await api.post('/auth/logout/', { refresh })
    } catch {}
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
  },

  // Поточний юзер
  fetchMe: async () => {
    try {
      const { data } = await api.get('/auth/me/')
      set({ user: data, isAuthenticated: true })
    } catch {
      set({ user: null, isAuthenticated: false })
    }
  },

  clearError: () => set({ error: null }),
}))

export default useAuthStore
