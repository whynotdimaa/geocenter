import { useTranslation } from 'react-i18next'
import { useState } from 'react'
import LocationComments from './LocationComments'
import AddToCollection from './AddToCollection'
import styles from './LocationList.module.css'

export default function LocationList({ locations, selected, onSelect, onEdit, onDelete, currentUser }) {
  const { t } = useTranslation()
  const [commentsModal, setCommentsModal] = useState({ isOpen: false, location: null })

  if (!locations.length) {
    return (
      <div className={styles.empty}>
        {t('locations.not_found')}
      </div>
    )
  }

  return (
    <>
      <div className={styles.list}>
        {locations.map((loc) => {
          const isOwner = currentUser && loc.owner === currentUser.email
          const isSelected = selected?.id === loc.id

          return (
            <div
              key={loc.id}
              className={`${styles.item} ${isSelected ? styles.itemSelected : ''}`}
              onClick={() => onSelect(loc)}
            >
              <div className={styles.itemIcon}>
                {loc.category?.icon || '◈'}
              </div>
              <div className={styles.itemBody}>
                <div className={styles.itemTop}>
                  <span className={styles.itemTitle}>{loc.title.toUpperCase()}</span>
                  {loc.category && (
                    <span
                      className={styles.itemBadge}
                      style={{ borderColor: loc.category.color, color: loc.category.color }}
                    >
                      {loc.category.name.toUpperCase()}
                    </span>
                  )}
                </div>
                <p className={styles.itemDesc}>
                  {loc.description || t('locations.no_desc')}
                </p>
                <div className={styles.itemMeta}>
                  <span>{loc.lat?.toFixed(4)}, {loc.lng?.toFixed(4)}</span>
                  {!loc.is_public && <span className={styles.private}>{t('locations.private')}</span>}
                </div>
                {/* Кнопки дій */}
                <div onClick={(e) => e.stopPropagation()}>
                  <button
                    className={styles.commentsBtn}
                    onClick={() => setCommentsModal({ isOpen: true, location: loc })}
                  >
                    💬 Коментарі
                  </button>
                  {currentUser && <AddToCollection locationId={loc.id} />}
                </div>
              </div>

              {isOwner && isSelected && (
                <div className={styles.itemActions} onClick={(e) => e.stopPropagation()}>
                  <button className={styles.editBtn} onClick={() => onEdit(loc)}>✎</button>
                  <button className={styles.deleteBtn} onClick={() => onDelete(loc.id)}>✕</button>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Модал коментарів */}
      <LocationComments
        locationId={commentsModal.location?.id}
        locationTitle={commentsModal.location?.title}
        currentUser={currentUser}
        isOpen={commentsModal.isOpen}
        onClose={() => setCommentsModal({ isOpen: false, location: null })}
      />
    </>
  )
}
