import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'
import styles from './AuthPage.module.css'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { login, loading, error, clearError } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    await login(email, password)
    if (useAuthStore.getState().isAuthenticated) {
      navigate('/')
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>⊕</span>
          <span className={styles.logoText}>GeoCenter</span>
        </div>

        <h1 className={styles.title}>Вхід</h1>

        {error && (
          <div className={styles.error} onClick={clearError}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label className={styles.label}>Email</label>
            <input
              className={styles.input}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              autoFocus
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Пароль</label>
            <input
              className={styles.input}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button className={styles.btn} type="submit" disabled={loading}>
            {loading ? 'Входимо...' : 'Увійти'}
          </button>
        </form>

        <p className={styles.footer}>
          Немає акаунту?{' '}
          <Link to="/register" className={styles.link}>
            Зареєструватись
          </Link>
        </p>
      </div>
    </div>
  )
}
