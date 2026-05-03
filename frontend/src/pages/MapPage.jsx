import { useState, useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents, useMap } from 'react-leaflet'
import { Link } from 'react-router-dom'
import L from 'leaflet'
import useAuthStore from '../store/authStore'
import { locationsApi, analyticsApi } from '../api/locations'
import LocationList from '../components/LocationList'
import LocationModal from '../components/LocationModal'
import styles from './MapPage.module.css'

// Фікс іконок Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// Кастомний маркер за кольором категорії — поза компонентом, це звичайна функція
function createCategoryIcon(color = '#2d6a4f', isSelected = false) {
  const size = isSelected ? 38 : 30
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 30 30">
      <circle cx="15" cy="13" r="9" fill="${color}" stroke="white" stroke-width="2.5"/>
      <circle cx="15" cy="13" r="4" fill="white" opacity="0.6"/>
      <line x1="15" y1="22" x2="15" y2="29" stroke="${color}" stroke-width="2.5" stroke-linecap="round"/>
    </svg>
  `
  return L.divIcon({
    html: svg,
    className: '',
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size],
  })
}

// Компонент теплової карти — поза MapPage, але це React-компонент, хуки тут ок
function HeatmapLayer({ points }) {
  const map = useMap()
  const heatRef = useRef(null)

  useEffect(() => {
    if (!points.length) return
    if (!L.heatLayer) return

    const heatData = points.map(p => [p.lat, p.lng, p.weight])

    if (heatRef.current) {
      map.removeLayer(heatRef.current)
    }

    heatRef.current = L.heatLayer(heatData, {
      radius: 50,
      blur: 40,
      maxZoom: 17,
      max: 5,          // ← зменшили max, тому кольори яскравіші
      minOpacity: 0.5, // ← мінімальна прозорість
      gradient: {
        0.0: '#00ff00',  // зелений
        0.4: '#ffff00',  // жовтий
        0.7: '#ff8000',  // помаранчевий
        1.0: '#ff0000',  // червоний
  },
}).addTo(map)

    return () => {
      if (heatRef.current) {
        map.removeLayer(heatRef.current)
        heatRef.current = null
      }
    }
  }, [points, map])

  return null
}

// Компонент для кліку на карту
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng)
    },
  })
  return null
}

// Константа поза компонентом — ок
const MAP_MODES = {
  MARKERS: 'markers',
  HEATMAP: 'heatmap',
  BOTH: 'both',
}

export default function MapPage() {
  // ✅ ВСІ useState і useEffect тільки всередині компонента
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  const [locations, setLocations] = useState([])
  const [categories, setCategories] = useState([])
  const [heatmapPoints, setHeatmapPoints] = useState([])
  const [heatPluginReady, setHeatPluginReady] = useState(false)
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [loading, setLoading] = useState(false)
  const [mapMode, setMapMode] = useState(MAP_MODES.MARKERS)
  const [modal, setModal] = useState(null)
  const [selected, setSelected] = useState(null)

  const mapRef = useRef()

  // Завантаження leaflet.heat плагіну
  useEffect(() => {
    import('leaflet.heat').then(() => {
      setHeatPluginReady(true)
    }).catch(err => {
      console.error('leaflet.heat не завантажився:', err)
    })
  }, [])

  // Завантаження локацій з debounce + AbortController
  useEffect(() => {
    const controller = new AbortController()
    const t = setTimeout(() => fetchLocations(controller.signal), 300)
    return () => { clearTimeout(t); controller.abort() }
  }, [search, selectedCategory])

  // Завантаження теплової карти при переключенні режиму
  useEffect(() => {
    if (mapMode === MAP_MODES.HEATMAP || mapMode === MAP_MODES.BOTH) {
      fetchHeatmap()
    }
  }, [mapMode])

  // Категорії завантажуємо один раз
  useEffect(() => {
    fetchCategories()
  }, [])

  const fetchLocations = async (signal) => {
    setLoading(true)
    try {
      const params = {}
      if (search) params.search = search
      if (selectedCategory) params.category = selectedCategory
      const { data } = await locationsApi.list(params, signal)
      setLocations(data.results || data)
    } catch (e) {
      if (e.name !== 'CanceledError') console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const fetchHeatmap = async () => {
  try {
    const { data } = await analyticsApi.heatmap()
    setHeatmapPoints(data.points || [])
  } catch (e) {
    console.error('Heatmap error:', e)
  }
}

  const fetchCategories = async () => {
    try {
      const { data } = await locationsApi.categories()
      setCategories(data.results || data)
    } catch {}
  }

  const handleMapClick = (latlng) => {
    if (!user) return
    setModal({ mode: 'create', latlng })
  }

  const handleSelectLocation = (loc) => {
    setSelected(loc)
    if (mapRef.current) {
      mapRef.current.setView([loc.lat, loc.lng], 15)
    }
  }

  const handleSaved = () => {
    setModal(null)
    fetchLocations(new AbortController().signal)
  }

  const handleDelete = async (id) => {
    if (!confirm('Видалити локацію?')) return
    await locationsApi.remove(id)
    setSelected(null)
    fetchLocations(new AbortController().signal)
  }

  const showMarkers = mapMode === MAP_MODES.MARKERS || mapMode === MAP_MODES.BOTH
  const showHeatmap = mapMode === MAP_MODES.HEATMAP || mapMode === MAP_MODES.BOTH

  return (
    <div className={styles.layout}>
      {/* ── Ліва панель ── */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <div className={styles.logo}>
            <span className={styles.logoIcon}>⊕</span>
            <span className={styles.logoText}>Geocenter</span>
          </div>
          <div className={styles.headerActions}>
            <button
              className={styles.addBtn}
              title="Додати локацію"
              onClick={() => setModal({ mode: 'create', latlng: null })}
            >
              +
            </button>
            <Link to="/collections" className={styles.iconBtn} title="Колекції">☰</Link>
            <Link to="/profile" className={styles.iconBtn} title="Профіль">◉</Link>
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

        {/* Перемикач режиму карти */}
        <div className={styles.mapModeWrap}>
          <span className={styles.mapModeLabel}>РЕЖИМ:</span>
          <div className={styles.mapModeBtns}>
            <button
              className={`${styles.modeBtn} ${mapMode === MAP_MODES.MARKERS ? styles.modeBtnActive : ''}`}
              onClick={() => setMapMode(MAP_MODES.MARKERS)}
              title="Маркери"
            >
              ◉
            </button>
            <button
              className={`${styles.modeBtn} ${mapMode === MAP_MODES.HEATMAP ? styles.modeBtnActive : ''}`}
              onClick={() => setMapMode(MAP_MODES.HEATMAP)}
              title="Теплова карта"
            >
              ▣
            </button>
            <button
              className={`${styles.modeBtn} ${mapMode === MAP_MODES.BOTH ? styles.modeBtnActive : ''}`}
              onClick={() => setMapMode(MAP_MODES.BOTH)}
              title="Обидва"
            >
              ◈
            </button>
          </div>
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
              onClick={() => setSelectedCategory(cat.id)}
            >
              <span className={styles.catDot} style={{ background: cat.color }} />
              {cat.name.toUpperCase()}
            </button>
          ))}
        </div>

        <div className={styles.count}>
          ENTRIES_FOUND: {locations.length}
          {loading && <span className={styles.loadingDot}> •</span>}
        </div>

        <LocationList
          locations={locations}
          selected={selected}
          onSelect={handleSelectLocation}
          onEdit={(loc) => setModal({ mode: 'edit', location: loc })}
          onDelete={handleDelete}
          currentUser={user}
        />

        <div className={styles.sidebarFooter}>
          <span className={styles.footerUser}>{user?.email}</span>
          <button className={styles.logoutBtn} onClick={logout}>Вийти</button>
        </div>
      </aside>

      {/* ── Карта ── */}
      <main className={styles.mapWrap}>
        <MapContainer
          center={[49.84, 24.03]}
          zoom={12}
          ref={mapRef}
          className={styles.map}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />

          <MapClickHandler onMapClick={handleMapClick} />

          {/* Теплова карта */}
          {showHeatmap && heatPluginReady && heatmapPoints.length > 0 && (
            <HeatmapLayer points={heatmapPoints} />
          )}

          {/* Маркери */}
          {showMarkers && locations.map((loc) => (
            <Marker
              key={loc.id}
              position={[loc.lat, loc.lng]}
              icon={createCategoryIcon(
                loc.category?.color || '#2d6a4f',
                selected?.id === loc.id
              )}
              eventHandlers={{ click: () => handleSelectLocation(loc) }}
            >
              <Popup>
                <div style={{ minWidth: 160 }}>
                  <strong style={{ fontSize: 13 }}>{loc.title}</strong>
                  {loc.description && (
                    <p style={{ fontSize: 12, margin: '4px 0 0', color: '#666' }}>
                      {loc.description}
                    </p>
                  )}
                  {loc.category && (
                    <span style={{
                      display: 'inline-block',
                      marginTop: 6,
                      fontSize: 11,
                      padding: '2px 8px',
                      borderRadius: 10,
                      background: loc.category.color + '22',
                      color: loc.category.color,
                      border: `1px solid ${loc.category.color}`,
                      fontWeight: 600,
                    }}>
                      {loc.category.name}
                    </span>
                  )}
                  <div style={{ fontSize: 11, color: '#999', marginTop: 6, fontFamily: 'monospace' }}>
                    {loc.lat?.toFixed(5)}, {loc.lng?.toFixed(5)}
                  </div>
                </div>
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