import styles from './LocationList.module.css'

export default function LocationList({ locations, selected, onSelect, onEdit, onDelete, currentUser }) {
  if (!locations.length) {
    return (
      <div className={styles.empty}>
        Локацій не знайдено
      </div>
    )
  }

  return (
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
                {loc.description || 'No description provided.'}
              </p>
              <div className={styles.itemMeta}>
                <span>{loc.lat?.toFixed(4)}, {loc.lng?.toFixed(4)}</span>
                {!loc.is_public && <span className={styles.private}>приватна</span>}
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
  )
}
