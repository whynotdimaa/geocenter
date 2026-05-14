import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { collectionsApi } from '../api/locations'
import styles from './CollectionsPage.module.css'

export default function CollectionsPage() {
  const { t } = useTranslation()
  const [collections, setCollections] = useState([])
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState('')
  const [inviteToken, setInviteToken] = useState('')
  const [inviteLink, setInviteLink] = useState(null)

  const fetchCollections = async () => {
    setLoading(true)
    try {
      const { data } = await collectionsApi.list()
      setCollections(data.results || data)
    } catch {}
    finally { setLoading(false) }
  }

  useEffect(() => { fetchCollections() }, [])

  const createCollection = async (e) => {
    e.preventDefault()
    if (!newName.trim()) return
    try {
      await collectionsApi.create({ name: newName, is_public: false })
      setNewName('')
      setCreating(false)
      fetchCollections()
    } catch {}
  }

  const deleteCollection = async (id) => {
    if (!confirm(t('collections.delete_confirm'))) return
    await collectionsApi.remove(id)
    fetchCollections()
  }

  const getInviteLink = async (id) => {
    const { data } = await collectionsApi.inviteLink(id)
    setInviteLink(data.invite_url)
  }

  const joinByToken = async (e) => {
    e.preventDefault()
    // Витягуємо UUID з рядка (або повного URL, або просто токену)
    const uuidMatch = inviteToken.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i)
    const token = uuidMatch ? uuidMatch[0] : inviteToken.trim()
    try {
      await collectionsApi.join(token)
      setInviteToken('')
      fetchCollections()
      alert(t('collections.joined_success'))
    } catch (err) {
      alert(err.response?.data?.detail || t('collections.invalid_token'))
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <div className={styles.header}>
          <Link to="/" className={styles.back}>{t('profile.back_to_map')}</Link>
          <h1 className={styles.title}>{t('collections.title')}</h1>
        </div>

        {/* Приєднатись за токеном */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>{t('collections.join_title')}</h2>
          <form onSubmit={joinByToken} className={styles.joinForm}>
            <input className={styles.input} value={inviteToken}
              onChange={(e) => setInviteToken(e.target.value)}
              placeholder={t('collections.join_placeholder')} />
            <button className={styles.btn} type="submit">{t('collections.join_btn')}</button>
          </form>
        </div>

        {/* Створити колекцію */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>{t('collections.title')}</h2>
            <button className={styles.addBtn} onClick={() => setCreating(true)}>{t('collections.new_btn')}</button>
          </div>

          {creating && (
            <form onSubmit={createCollection} className={styles.createForm}>
              <input className={styles.input} value={newName} autoFocus
                onChange={(e) => setNewName(e.target.value)}
                placeholder={t('collections.name_placeholder')} required />
              <button className={styles.btn} type="submit">{t('collections.create_btn')}</button>
              <button className={styles.cancelBtn} type="button"
                onClick={() => setCreating(false)}>{t('collections.cancel_btn')}</button>
            </form>
          )}

          {loading ? (
            <p className={styles.empty}>{t('collections.loading')}</p>
          ) : collections.length === 0 ? (
            <p className={styles.empty}>{t('collections.empty_collections')}</p>
          ) : (
            <div className={styles.list}>
              {collections.map((col) => (
                <div key={col.id} className={styles.item}>
                  <div className={styles.itemBody}>
                    <div className={styles.itemTop}>
                      <span className={styles.itemName}>{col.name}</span>
                      <span className={styles.itemRole}>{col.user_role}</span>
                      {col.is_public && <span className={styles.publicBadge}>{t('collections.public_badge')}</span>}
                    </div>
                    <div className={styles.itemMeta}>
                      {col.locations_count} {t('collections.locations_count')} · {col.members_count} {t('collections.members_count')}
                    </div>
                  </div>
                  <div className={styles.itemActions}>
                    {col.user_role === 'owner' && (
                      <>
                        <button className={styles.linkBtn}
                          onClick={() => getInviteLink(col.id)}
                          title="Отримати посилання-запрошення">
                          🔗
                        </button>
                        <button className={styles.deleteBtn}
                          onClick={() => deleteCollection(col.id)}>
                          ✕
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {inviteLink && (
            <div className={styles.inviteLinkBox}>
              <span className={styles.inviteLinkLabel}>{t('collections.invite_label')}</span>
              <input className={styles.inviteLinkInput} value={inviteLink} readOnly
                onClick={(e) => e.target.select()} />
              <button className={styles.copyBtn}
                onClick={() => { navigator.clipboard.writeText(inviteLink); setInviteLink(null) }}>
                {t('collections.copy_btn')}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
