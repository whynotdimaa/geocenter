import { useState, useEffect } from 'react'
import { locationsApi } from '../api/locations'
import { useTranslation } from 'react-i18next'
import styles from './LocationModal.module.css'

export default function LocationModal({ mode, latlng, location, address: prefilledAddress, categories, onSave, onClose }) {
  const { t } = useTranslation()
  const isEdit = mode === 'edit'

  const [form, setForm] = useState({
    title: '',
    description: '',
    latitude: '',
    longitude: '',
    category_id: '',
    is_public: true,
    address: '',
    altitude: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (isEdit && location) {
      setForm({
        title: location.title,
        description: location.description || '',
        latitude: location.lat,
        longitude: location.lng,
        category_id: location.category?.id || '',
        is_public: location.is_public,
        address: location.address || '',
        altitude: location.altitude || '',
      })
    } else if (latlng) {
      setForm((f) => ({
        ...f,
        latitude: latlng.lat.toFixed(6),
        longitude: latlng.lng.toFixed(6),
        address: prefilledAddress || '',
      }))
    }
  }, [])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm({ ...form, [name]: type === 'checkbox' ? checked : value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const payload = {
      title: form.title,
      description: form.description,
      latitude: parseFloat(form.latitude),
      longitude: parseFloat(form.longitude),
      is_public: form.is_public,
      address: form.address,
    }
    if (form.category_id) payload.category_id = parseInt(form.category_id)
    if (form.altitude) payload.altitude = parseFloat(form.altitude)

    try {
      if (isEdit) {
        await locationsApi.update(location.id, payload)
      } else {
        await locationsApi.create(payload)
      }
      onSave()
    } catch (err) {
      const data = err.response?.data
      setError(data ? Object.values(data).flat().join(' ') : t('profile.msg_save_error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2 className={styles.title}>
            {isEdit ? t('locations.edit_title') : t('locations.new_title')}
          </h2>
          <button className={styles.closeBtn} onClick={onClose}>✕</button>
        </div>

        {error && <div className={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.row}>
            <div className={styles.field}>
              <label className={styles.label}>{t('locations.name')}</label>
              <input className={styles.input} name="title" value={form.title}
                onChange={handleChange} placeholder={t('locations.name')} required />
            </div>
          </div>

          <div className={styles.row}>
            <div className={styles.field}>
              <label className={styles.label}>{t('locations.latitude')}</label>
              <input className={styles.input} name="latitude" value={form.latitude}
                onChange={handleChange} placeholder="50.4501" required type="number" step="any" />
            </div>
            <div className={styles.field}>
              <label className={styles.label}>{t('locations.longitude')}</label>
              <input className={styles.input} name="longitude" value={form.longitude}
                onChange={handleChange} placeholder="30.5234" required type="number" step="any" />
            </div>
          </div>

          <div className={styles.row}>
            <div className={styles.field}>
              <label className={styles.label}>{t('locations.category')}</label>
              <select className={styles.input} name="category_id" value={form.category_id}
                onChange={handleChange}>
                <option value="">{t('locations.no_category')}</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
            <div className={styles.field}>
              <label className={styles.label}>{t('locations.altitude')}</label>
              <input className={styles.input} name="altitude" value={form.altitude}
                onChange={handleChange} placeholder={t('locations.optional')} type="number" step="any" />
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>{t('locations.address')}</label>
            <input className={styles.input} name="address" value={form.address}
              onChange={handleChange} placeholder="вул. Хрещатик, 1, Київ" />
          </div>

          <div className={styles.field}>
            <label className={styles.label}>{t('locations.description')}</label>
            <textarea className={styles.textarea} name="description" value={form.description}
              onChange={handleChange} placeholder={t('locations.desc_placeholder')} rows={3} />
          </div>

          <div className={styles.checkboxRow}>
            <input type="checkbox" id="is_public" name="is_public"
              checked={form.is_public} onChange={handleChange} />
            <label htmlFor="is_public" className={styles.checkboxLabel}>
              {t('locations.is_public')}
            </label>
          </div>

          <div className={styles.actions}>
            <button type="button" className={styles.cancelBtn} onClick={onClose}>
              {t('locations.cancel_btn')}
            </button>
            <button type="submit" className={styles.saveBtn} disabled={loading}>
              {loading ? t('profile.saving') : isEdit ? t('locations.save_btn') : t('locations.add_btn')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
