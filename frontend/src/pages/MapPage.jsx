import { useState, useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet'
import { Link } from 'react-router-dom'
import L from 'leaflet'
import useAuthStore from '../store/authStore'
import { locationsApi } from '../api/locations'
import LocationList from '../components/LocationList'
import LocationModal from '../components/LocationModal'
import styles from './MapPage.module.css'

// Фікс іконок Leaflet при використанні з Vite
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// Компонент для кліку на карту — додає нову точку
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng)
    },
  })
  return null
}

export default function MapPage() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  const [locations, setLocations] = useState([])
  const [categories, setCategories] = useState([])
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [loading, setLoading] = useState(false)

  // Модалка: null = закрита, { mode: 'create', latlng } або { mode: 'edit', location }
  const [modal, setModal] = useState(null)
  const [selected, setSelected] = useState(null)

  const mapRef = useRef()

  const fetchLocations = async () => {
    setLoading(true)
    try {
      const params = {}
      if (search) params.search = search
      if (selectedCategory) params.category = selectedCategory
      const { data } = await locationsApi.list(params)
      setLocations(data.results || data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const fetchCategories = async () => {
    try {
      const { data } = await locationsApi.categories()
      setCategories(data.results || data)
    } catch {}
  }

  useEffect(() => {
    fetchCategories()
  }, [])

  useEffect(() => {
    const t = setTimeout(fetchLocations, 300)
    return () => clearTimeout(t)
  }, [search, selectedCategory])

  const handleMapClick = (latlng) => {
    if (!user) return
    setModal({ mode: 'create', latlng })
  }

  const handleSelectLocation = (loc) => {
    setSelected(loc)
    // Центруємо карту на точці
    if (mapRef.current) {
      mapRef.current.setView([loc.lat, loc.lng], 14)
    }
  }

  const handleSaved = () => {
    setModal(null)
    fetchLocations()
  }

  const handleDelete = async (id) => {
    if (!confirm('Видалити локацію?')) return
    await locationsApi.remove(id)
    setSelected(null)
    fetchLocations()
  }

  return (
    <div className={styles.layout}>
      {/* ── Ліва панель ── */}
      <aside className={styles.sidebar}>
        {/* Хедер */}
        <div className={styles.sidebarHeader}>
          <div className={styles.logo}>
            <span className={styles.logoIcon}>⊕</span>
            <span className={styles.logoText}>Geocenter</span>
          </div>
          <div className={styles.headerActions}>
            <button
              className={styles.addBtn}
              title="Додати локацію (або клікни на карту)"
              onClick={() => setModal({ mode: 'create', latlng: null })}
            >
              +
            </button>
            <Link to="/collections" className={styles.iconBtn} title="Колекції">
              ☰
            </Link>
            <Link to="/profile" className={styles.iconBtn} title="Профіль">
              ◉
            </Link>
          </div>
        </div>

        {/* Пошук */}
        <div className={styles.searchWrap}>
          <input
            className={styles.searchInput}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="SEARCH REGISTRY..."
          />
        </div>

        {/* Фільтр по категоріях */}
        <div className={styles.categories}>
          <button
            className={`${styles.catBtn} ${selectedCategory === '' ? styles.catActive : ''}`}
            onClick={() => setSelectedCategory('')}
          >
            ALL_UNITS
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              className={`${styles.catBtn} ${selectedCategory == cat.id ? styles.catActive : ''}`}
              style={{ '--cat-color': cat.color }}
              onClick={() => setSelectedCategory(cat.id)}
            >
              <span className={styles.catDot} style={{ background: cat.color }} />
              {cat.name.toUpperCase()}
            </button>
          ))}
        </div>

        {/* Лічильник */}
        <div className={styles.count}>
          ENTRIES_FOUND: {locations.length}
          {loading && <span className={styles.loadingDot}> •</span>}
        </div>

        {/* Список локацій */}
        <LocationList
          locations={locations}
          selected={selected}
          onSelect={handleSelectLocation}
          onEdit={(loc) => setModal({ mode: 'edit', location: loc })}
          onDelete={handleDelete}
          currentUser={user}
        />

        {/* Футер */}
        <div className={styles.sidebarFooter}>
          <span className={styles.footerUser}>{user?.email}</span>
          <button className={styles.logoutBtn} onClick={logout}>
            Вийти
          </button>
        </div>
      </aside>

      {/* ── Карта ── */}
      <main className={styles.mapWrap}>
        <MapContainer
          center={[50.45, 30.52]}
          zoom={7}
          ref={mapRef}
          className={styles.map}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          <MapClickHandler onMapClick={handleMapClick} />

          {locations.map((loc) => (
            <Marker
              key={loc.id}
              position={[loc.lat, loc.lng]}
              eventHandlers={{ click: () => handleSelectLocation(loc) }}
            >
              <Popup>
                <strong>{loc.title}</strong>
                {loc.description && <p>{loc.description}</p>}
                {loc.category && (
                  <span style={{ color: loc.category.color }}>
                    {loc.category.name}
                  </span>
                )}
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </main>

      {/* ── Модалка ── */}
      {modal && (
        <LocationModal
          mode={modal.mode}
          latlng={modal.latlng}
          location={modal.location}
          categories={categories}
          onSave={handleSaved}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  )
}
