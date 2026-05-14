import { useState, useEffect, useRef } from 'react'
import { collectionsApi } from '../api/locations'
import styles from './AddToCollection.module.css'

export default function AddToCollection({ locationId }) {
  const [open, setOpen] = useState(false)
  const [collections, setCollections] = useState([])
  const [loading, setLoading] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    function onClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    if (open) document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [open])

  const handleOpen = async (e) => {
    e.stopPropagation()
    if (open) {
      setOpen(false)
      return
    }
    setOpen(true)
    setLoading(true)
    try {
      const { data } = await collectionsApi.list()
      const list = data.results || data
      // Тільки ті де власник або редактор
      setCollections(list.filter((c) => c.user_role === 'owner' || c.user_role === 'editor'))
    } catch {
      setCollections([])
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = async (collectionId, e) => {
    e.stopPropagation()
    try {
      await collectionsApi.addLocation(collectionId, locationId)
      alert('✓ Локацію додано до колекції')
      setOpen(false)
    } catch (err) {
      alert(err.response?.data?.detail || 'Помилка додавання')
    }
  }

  return (
    <div className={styles.wrapper} ref={ref}>
      <button className={styles.btn} onClick={handleOpen}>
        📁 У колекцію
      </button>
      {open && (
        <div className={styles.dropdown}>
          {loading && <div className={styles.empty}>Завантаження…</div>}
          {!loading && collections.length === 0 && (
            <div className={styles.empty}>Немає колекцій</div>
          )}
          {!loading && collections.map((c) => (
            <button
              key={c.id}
              className={styles.item}
              onClick={(e) => handleAdd(c.id, e)}
            >
              {c.name}
              <span className={styles.role}>{c.user_role}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
