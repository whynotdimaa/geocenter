import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import useAuthStore from '../store/authStore'
import styles from './AuthPage.module.css'

export default function RegisterPage() {
  const { t } = useTranslation()
  const [form, setForm] = useState({ username: '', email: '', password: '', password2: '' })
  const { register, loading, error, clearError } = useAuthStore()
  const navigate = useNavigate()

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    await register(form.username, form.email, form.password, form.password2)
    if (useAuthStore.getState().isAuthenticated) navigate('/')
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>⊕</span>
          <span className={styles.logoText}>GeoCenter</span>
        </div>

        <h1 className={styles.title}>{t('auth.register_title')}</h1>

        {error && (
          <div className={styles.error} onClick={clearError}>{error}</div>
        )}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label className={styles.label}>{t('auth.username')}</label>
            <input className={styles.input} name="username" value={form.username}
              onChange={handleChange} placeholder="username" required />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>{t('auth.email')}</label>
            <input className={styles.input} type="email" name="email" value={form.email}
              onChange={handleChange} placeholder="your@email.com" required />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>{t('auth.password')}</label>
            <input className={styles.input} type="password" name="password" value={form.password}
              onChange={handleChange} placeholder="мін. 8 символів" required />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>{t('profile.confirm_password')}</label>
            <input className={styles.input} type="password" name="password2" value={form.password2}
              onChange={handleChange} placeholder="повтори пароль" required />
          </div>

          <button className={styles.btn} type="submit" disabled={loading}>
            {loading ? t('auth.registering') : t('auth.register_btn')}
          </button>
        </form>

        <p className={styles.footer}>
          <Link to="/login" className={styles.link}>{t('auth.has_account')}</Link>
        </p>
      </div>
    </div>
  )
}
