import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { collectionsApi } from '../api/locations'
import styles from './CollectionsPage.module.css'

export default function CollectionsPage() {
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
    if (!confirm('Видалити колекцію?')) return
    await collectionsApi.remove(id)
    fetchCollections()
  }

  const getInviteLink = async (id) => {
    const { data } = await collectionsApi.inviteLink(id)
    setInviteLink(data.invite_url)
  }

  const joinByToken = async (e) => {
    e.preventDefault()
    try {
      await collectionsApi.join(inviteToken)
      setInviteToken('')
      fetchCollections()
      alert('Ви приєднались до колекції!')
    } catch (err) {
      alert(err.response?.data?.detail || 'Невірний токен')
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <div className={styles.header}>
          <Link to="/" className={styles.back}>← Карта</Link>
          <h1 className={styles.title}>Колекції</h1>
        </div>

        {/* Приєднатись за токеном */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Приєднатись за запрошенням</h2>
          <form onSubmit={joinByToken} className={styles.joinForm}>
            <input className={styles.input} value={inviteToken}
              onChange={(e) => setInviteToken(e.target.value)}
              placeholder="Вставте токен-запрошення..." />
            <button className={styles.btn} type="submit">Приєднатись</button>
          </form>
        </div>

        {/* Створити колекцію */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Мої колекції</h2>
            <button className={styles.addBtn} onClick={() => setCreating(true)}>+ Нова</button>
          </div>

          {creating && (
            <form onSubmit={createCollection} className={styles.createForm}>
              <input className={styles.input} value={newName} autoFocus
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Назва колекції" required />
              <button className={styles.btn} type="submit">Створити</button>
              <button className={styles.cancelBtn} type="button"
                onClick={() => setCreating(false)}>Скасувати</button>
            </form>
          )}

          {loading ? (
            <p className={styles.empty}>Завантаження...</p>
          ) : collections.length === 0 ? (
            <p className={styles.empty}>У вас ще немає колекцій</p>
          ) : (
            <div className={styles.list}>
              {collections.map((col) => (
                <div key={col.id} className={styles.item}>
                  <div className={styles.itemBody}>
                    <div className={styles.itemTop}>
                      <span className={styles.itemName}>{col.name}</span>
                      <span className={styles.itemRole}>{col.user_role}</span>
                      {col.is_public && <span className={styles.publicBadge}>публічна</span>}
                    </div>
                    <div className={styles.itemMeta}>
                      {col.locations_count} локацій · {col.members_count} учасників
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
              <span className={styles.inviteLinkLabel}>Посилання-запрошення:</span>
              <input className={styles.inviteLinkInput} value={inviteLink} readOnly
                onClick={(e) => e.target.select()} />
              <button className={styles.copyBtn}
                onClick={() => { navigator.clipboard.writeText(inviteLink); setInviteLink(null) }}>
                Копіювати
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
