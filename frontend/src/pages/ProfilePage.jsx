import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../api/axios'
import useAuthStore from '../store/authStore'
import styles from './ProfilePage.module.css'

export default function ProfilePage() {
  const { t } = useTranslation()
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
      await api.patch('/users/me', { ...form, profile })
      await fetchMe()
      setMsg({ type: 'ok', text: t('profile.msg_profile_saved') })
    } catch (err) {
      const detail = err.response?.data?.detail
      let text = t('profile.msg_save_error')
      if (Array.isArray(detail)) {
        text = detail.map(e => e.msg).join(', ')
      } else if (typeof detail === 'string') {
        text = detail
      }
      setMsg({ type: 'err', text })
    } finally {
      setLoading(false)
    }
  }

  const changePassword = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/users/me/change-password', pwForm)
      setPwForm({ old_password: '', new_password: '', new_password2: '' })
      setMsg({ type: 'ok', text: t('profile.msg_pwd_changed') })
    } catch (err) {
      const detail = err.response?.data?.detail
      let text = t('profile.msg_error')
      if (Array.isArray(detail)) {
        text = detail.map(e => e.msg).join(', ')
      } else if (typeof detail === 'string') {
        text = detail
      }
      setMsg({ type: 'err', text })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <div className={styles.header}>
          <Link to="/" className={styles.back}>{t('profile.back_to_map')}</Link>
          <h1 className={styles.title}>{t('profile.title')}</h1>
        </div>

        {msg && (
          <div className={`${styles.msg} ${msg.type === 'ok' ? styles.msgOk : styles.msgErr}`}
            onClick={() => setMsg(null)}>
            {msg.text}
          </div>
        )}

        {/* Основна інформація */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>{t('profile.basic_info')}</h2>
          <form onSubmit={saveProfile} className={styles.form}>
            <div className={styles.field}>
              <label className={styles.label}>{t('auth.email')}</label>
              <input className={`${styles.input} ${styles.inputDisabled}`}
                value={user?.email || ''} disabled />
            </div>
            <div className={styles.field}>
              <label className={styles.label}>{t('auth.username')}</label>
              <input className={styles.input} value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })} />
            </div>
            <div className={styles.field}>
              <label className={styles.label}>{t('profile.bio')}</label>
              <textarea className={styles.textarea} rows={3} value={form.bio}
                onChange={(e) => setForm({ ...form, bio: e.target.value })}
                placeholder={t('profile.bio_placeholder')} />
            </div>

            <h3 className={styles.subTitle}>{t('profile.settings')}</h3>
            <div className={styles.row}>
              <div className={styles.field}>
                <label className={styles.label}>{t('profile.language')}</label>
                <select className={styles.input} value={profile.language}
                  onChange={(e) => setProfile({ ...profile, language: e.target.value })}>
                  <option value="uk">{t('profile.lang_uk')}</option>
                  <option value="en">{t('profile.lang_en')}</option>
                </select>
              </div>
              <div className={styles.field}>
                <label className={styles.label}>{t('profile.coord_format')}</label>
                <select className={styles.input} value={profile.coord_units}
                  onChange={(e) => setProfile({ ...profile, coord_units: e.target.value })}>
                  <option value="decimal">{t('profile.coord_decimal')}</option>
                  <option value="dms">{t('profile.coord_dms')}</option>
                </select>
              </div>
            </div>

            <button className={styles.btn} type="submit" disabled={loading}>
              {loading ? t('profile.saving') : t('profile.save_btn')}
            </button>
          </form>
        </div>

        {/* Зміна пароля */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>{t('profile.change_password')}</h2>
          <form onSubmit={changePassword} className={styles.form}>
            <div className={styles.field}>
              <label className={styles.label}>{t('profile.current_password')}</label>
              <input className={styles.input} type="password"
                value={pwForm.old_password}
                onChange={(e) => setPwForm({ ...pwForm, old_password: e.target.value })} required />
            </div>
            <div className={styles.row}>
              <div className={styles.field}>
                <label className={styles.label}>{t('profile.new_password')}</label>
                <input className={styles.input} type="password"
                  value={pwForm.new_password}
                  onChange={(e) => setPwForm({ ...pwForm, new_password: e.target.value })} required />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>{t('profile.confirm_password')}</label>
                <input className={styles.input} type="password"
                  value={pwForm.new_password2}
                  onChange={(e) => setPwForm({ ...pwForm, new_password2: e.target.value })} required />
              </div>
            </div>
            <button className={styles.btn} type="submit" disabled={loading}>
              {t('profile.change_pwd_btn')}
            </button>
          </form>
        </div>

        <button className={styles.logoutBtn} onClick={logout}>
          {t('profile.logout')}
        </button>
      </div>
    </div>
  )
}
