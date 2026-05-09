import { useState, useEffect } from 'react'
import { locationsApi } from '../api/locations'
import styles from './LocationComments.module.css'

export default function LocationComments({ locationId, locationTitle, currentUser, isOpen, onClose }) {
  const [comments, setComments] = useState([])
  const [newComment, setNewComment] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (isOpen && locationId) {
      fetchComments()
    }
  }, [isOpen, locationId])

  const fetchComments = async () => {
    setLoading(true)
    try {
      const { data } = await locationsApi.getComments(locationId)
      setComments(data.results || data)
    } catch (err) {
      console.error('Failed to load comments:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!newComment.trim()) return

    setSubmitting(true)
    try {
      await locationsApi.addComment(locationId, newComment.trim())
      setNewComment('')
      fetchComments()
    } catch (err) {
      alert('Помилка при додаванні коментаря')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (commentId) => {
    if (!confirm('Видалити цей коментар?')) return
    try {
      await locationsApi.deleteComment(locationId, commentId)
      fetchComments()
    } catch (err) {
      alert('Помилка при видаленні')
    }
  }

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('uk-UA', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (!isOpen) return null

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div>
            <span className={styles.title}>💬 Коментарі</span>
            <span className={styles.count}>{comments.length}</span>
          </div>
          <button className={styles.closeBtn} onClick={onClose}>✕</button>
        </div>

        <div className={styles.locationInfo}>
          📍 {locationTitle}
        </div>

        {loading && <div className={styles.loading}>⏳ Завантаження...</div>}

        <div className={styles.list}>
          {comments.length === 0 && !loading && (
            <div className={styles.empty}>
              <div className={styles.emptyIcon}>💬</div>
              <div>Ще немає коментарів</div>
              <div className={styles.emptySub}>Будьте першим! 👋</div>
            </div>
          )}

          {comments.map((comment) => (
            <div key={comment.id} className={styles.comment}>
              <div className={styles.commentHeader}>
                <span className={styles.author}>👤 {comment.user}</span>
                <span className={styles.date}>{formatDate(comment.created_at)}</span>
              </div>
              <p className={styles.text}>{comment.text}</p>
              {currentUser?.email === comment.user && (
                <button
                  className={styles.deleteBtn}
                  onClick={() => handleDelete(comment.id)}
                  title="Видалити коментар"
                >
                  🗑️ Видалити
                </button>
              )}
            </div>
          ))}
        </div>

        {currentUser && (
          <form className={styles.form} onSubmit={handleSubmit}>
            <textarea
              className={styles.input}
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder='Напишіть коментар...'
              rows={3}
            />
            <button
              type="submit"
              className={styles.submitBtn}
              disabled={submitting || !newComment.trim()}
            >
              {submitting ? '⏳ Надсилання...' : '📨 Надіслати'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
