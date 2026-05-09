import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import useAuthStore from './store/authStore'

import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import MapPage from './pages/MapPage'
import ProfilePage from './pages/ProfilePage'
import CollectionsPage from './pages/CollectionsPage'
import AnalyticsPage from './pages/AnalyticsPage'


// Захищений маршрут — редіректить на /login якщо не авторизований
function PrivateRoute({ children }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default function App() {
  const fetchMe = useAuthStore((s) => s.fetchMe)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const user = useAuthStore((s) => s.user)
  const { i18n } = useTranslation()

  // Підтягуємо дані юзера при старті якщо є токен
  useEffect(() => {
    if (isAuthenticated) fetchMe()
  }, [])

  // Синхронізуємо мову з профілем
  useEffect(() => {
    if (user?.profile?.language) {
      i18n.changeLanguage(user.profile.language)
    }
  }, [user?.profile?.language, i18n])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route path="/" element={
          <PrivateRoute><MapPage /></PrivateRoute>
        } />
        <Route path="/profile" element={
          <PrivateRoute><ProfilePage /></PrivateRoute>
        } />
        <Route path="/collections" element={
          <PrivateRoute><CollectionsPage /></PrivateRoute>
        } />
        <Route path="/analytics" element={
          <PrivateRoute><AnalyticsPage /></PrivateRoute>
        } />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
