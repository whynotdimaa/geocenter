import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/axios'
import useAuthStore from '../store/authStore'
import styles from './ProfilePage.module.css'

export default function ProfilePage() {
  const { user, fetchMe, logout } = useAuthStore()
  const [form, setForm] = useState({ username: '', bio: '' })
  const [profile, setProfile] = useState({ language: 'uk', coord_units: 'decimal', dark_mode: false })
  const [pwForm, setPwForm] = useState({ old_password: '', new_password: '', new_password2: '' })
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) {
      setForm({ username: user.username || '', bio: user.bio || '' })
      if (user.profile) setProfile(user.profile)
    }
  }, [user])

  const saveProfile = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.patch('/auth/profile/', { ...form, profile })
      await fetchMe()
      setMsg({ type: 'ok', text: 'Профіль збережено' })
    } catch {
      setMsg({ type: 'err', text: 'Помилка збереження' })
    } finally {
      setLoading(false)
    }
  }

  const changePassword = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/auth/change-password/', pwForm)
      setPwForm({ old_password: '', new_password: '', new_password2: '' })
      setMsg({ type: 'ok', text: 'Пароль змінено' })
    } catch (err) {
      const data = err.response?.data
      setMsg({ type: 'err', text: data ? Object.values(data).flat().join(' ') : 'Помилка' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <div className={styles.header}>
          <Link to="/" className={styles.back}>← Повернутись до карти</Link>
          <h1 className={styles.title}>Профіль</h1>
        </div>

        {msg && (
          <div className={`${styles.msg} ${msg.type === 'ok' ? styles.msgOk : styles.msgErr}`}
            onClick={() => setMsg(null)}>
            {msg.text}
          </div>
        )}

        {/* Основна інформація */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Основна інформація</h2>
          <form onSubmit={saveProfile} className={styles.form}>
            <div className={styles.field}>
              <label className={styles.label}>Email</label>
              <input className={`${styles.input} ${styles.inputDisabled}`}
                value={user?.email || ''} disabled />
            </div>
            <div className={styles.field}>
              <label className={styles.label}>Імʼя користувача</label>
              <input className={styles.input} value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })} />
            </div>
            <div className={styles.field}>
              <label className={styles.label}>Bio</label>
              <textarea className={styles.textarea} rows={3} value={form.bio}
                onChange={(e) => setForm({ ...form, bio: e.target.value })}
                placeholder="Розкажи про себе..." />
            </div>

            <h3 className={styles.subTitle}>Налаштування</h3>
            <div className={styles.row}>
              <div className={styles.field}>
                <label className={styles.label}>Мова</label>
                <select className={styles.input} value={profile.language}
                  onChange={(e) => setProfile({ ...profile, language: e.target.value })}>
                  <option value="uk">Українська</option>
                  <option value="en">English</option>
                </select>
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Формат координат</label>
                <select className={styles.input} value={profile.coord_units}
                  onChange={(e) => setProfile({ ...profile, coord_units: e.target.value })}>
                  <option value="decimal">Десяткові градуси</option>
                  <option value="dms">Градуси/хвилини/секунди</option>
                </select>
              </div>
            </div>

            <button className={styles.btn} type="submit" disabled={loading}>
              {loading ? 'Зберігаємо...' : 'Зберегти профіль'}
            </button>
          </form>
        </div>

        {/* Зміна пароля */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Зміна пароля</h2>
          <form onSubmit={changePassword} className={styles.form}>
            <div className={styles.field}>
              <label className={styles.label}>Поточний пароль</label>
              <input className={styles.input} type="password"
                value={pwForm.old_password}
                onChange={(e) => setPwForm({ ...pwForm, old_password: e.target.value })} required />
            </div>
            <div className={styles.row}>
              <div className={styles.field}>
                <label className={styles.label}>Новий пароль</label>
                <input className={styles.input} type="password"
                  value={pwForm.new_password}
                  onChange={(e) => setPwForm({ ...pwForm, new_password: e.target.value })} required />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Підтвердження</label>
                <input className={styles.input} type="password"
                  value={pwForm.new_password2}
                  onChange={(e) => setPwForm({ ...pwForm, new_password2: e.target.value })} required />
              </div>
            </div>
            <button className={styles.btn} type="submit" disabled={loading}>
              Змінити пароль
            </button>
          </form>
        </div>

        <button className={styles.logoutBtn} onClick={logout}>
          Вийти з акаунту
        </button>
      </div>
    </div>
  )
}
