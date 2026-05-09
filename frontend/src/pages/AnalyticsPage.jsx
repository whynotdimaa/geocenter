import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { analyticsApi } from '../api/locations'
import styles from './AnalyticsPage.module.css'

export default function AnalyticsPage() {
  const [stats, setStats] = useState(null)
  const [viewMode, setViewMode] = useState('personal') // 'personal' | 'global'
  const [clusters, setClusters] = useState(null)
  const [nClusters, setNClusters] = useState(5)
  const [loadingCluster, setLoadingCluster] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    analyticsApi.stats().then(({ data }) => {
      setStats(data)
      setLoading(false)
    })
  }, [])

  const runClustering = async () => {
    setLoadingCluster(true)
    try {
      const { data } = await analyticsApi.cluster(nClusters)
      setClusters(data)
    } catch (e) {
      alert(e.response?.data?.error || 'Помилка кластеризації')
    } finally {
      setLoadingCluster(false)
    }
  }

  if (loading) return <div className={styles.loading}>Завантаження...</div>

  const currentStats = viewMode === 'personal' ? stats.personal : stats.global
  const maxViews = currentStats.most_viewed_location?.views || 1
  const topCats = currentStats.locations_by_category?.slice(0, 6) || []
  const maxCat = topCats[0]?.count || 1

  const isPersonal = viewMode === 'personal'

  return (
    <div className={styles.page}>
      <div className={styles.topbar}>
        <Link to="/" className={styles.back}>← Карта</Link>
        <h1 className={styles.title}>Аналітика</h1>
        <div className={styles.toggle}>
          <button
            className={`${styles.toggleBtn} ${isPersonal ? styles.active : ''}`}
            onClick={() => setViewMode('personal')}
          >
            Мої
          </button>
          <button
            className={`${styles.toggleBtn} ${!isPersonal ? styles.active : ''}`}
            onClick={() => setViewMode('global')}
          >
            Всі
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div className={styles.statsGrid}>
        <div className={styles.stat}>
          <div className={styles.statLabel}>{isPersonal ? 'Мої локації' : 'Всього локацій'}</div>
          <div className={styles.statVal}>{currentStats.total_locations}</div>
          <div className={styles.statSub}>+{currentStats.locations_last_30_days} за 30 днів</div>
        </div>
        <div className={styles.stat}>
          <div className={styles.statLabel}>{isPersonal ? 'Мої перегляди' : 'Всі перегляди'}</div>
          <div className={styles.statVal}>
            {isPersonal ? currentStats.total_views_received : currentStats.total_views}
          </div>
          <div className={styles.statSub}>{isPersonal ? 'отримано' : 'по всім локаціям'}</div>
        </div>
        {!isPersonal && (
          <div className={styles.stat}>
            <div className={styles.statLabel}>Користувачів</div>
            <div className={styles.statVal}>{currentStats.unique_users}</div>
            <div className={styles.statSub}>з локаціями</div>
          </div>
        )}
        {isPersonal && (
          <>
            <div className={styles.stat}>
              <div className={styles.statLabel}>Колекції</div>
              <div className={styles.statVal}>{currentStats.total_collections}</div>
              <div className={styles.statSub}>мої колекції</div>
            </div>
            <div className={styles.stat}>
              <div className={styles.statLabel}>Публічних</div>
              <div className={styles.statVal}>{currentStats.public_locations}</div>
              <div className={styles.statSub}>приватних: {currentStats.private_locations}</div>
            </div>
          </>
        )}
      </div>

      <div className={styles.row}>
        {/* Most viewed */}
        <div className={styles.card}>
          <div className={styles.cardTitle}>
            {isPersonal ? 'Моя найпопулярніша' : 'Найпопулярніша в системі'}
          </div>
          {currentStats.most_viewed_location ? (
            <div className={styles.mostViewed}>
              <div className={styles.mvName}>{currentStats.most_viewed_location.title}</div>
              <div className={styles.mvViews}>{currentStats.most_viewed_location.views} переглядів</div>
              <div className={styles.mvBar}>
                <div className={styles.mvBarFill} style={{ width: '100%' }} />
              </div>
            </div>
          ) : (
            <div className={styles.empty}>Ще немає переглядів</div>
          )}
        </div>

        {/* By category */}
        <div className={styles.card}>
          <div className={styles.cardTitle}>За категоріями</div>
          {topCats.length > 0 ? topCats.map((cat, i) => (
            <div key={i} className={styles.catRow}>
              <span className={styles.catName}>{cat.category__name || 'Без категорії'}</span>
              <div className={styles.catTrack}>
                <div
                  className={styles.catFill}
                  style={{ width: `${Math.round(cat.count / maxCat * 100)}%` }}
                />
              </div>
              <span className={styles.catCount}>{cat.count}</span>
            </div>
          )) : (
            <div className={styles.empty}>Немає даних</div>
          )}
        </div>
      </div>

      {/* Clustering */}
      <div className={styles.card} style={{ marginBottom: 0 }}>
        <div className={styles.cardHeader}>
          <div className={styles.cardTitle}>K-Means кластеризація публічних локацій</div>
          <div className={styles.clusterControls}>
            <label className={styles.clusterLabel}>
              Кластерів: <strong>{nClusters}</strong>
            </label>
            <input
              type="range" min="2" max="10" step="1"
              value={nClusters}
              onChange={e => setNClusters(Number(e.target.value))}
              className={styles.slider}
            />
            <button
              className={styles.runBtn}
              onClick={runClustering}
              disabled={loadingCluster}
            >
              {loadingCluster ? 'Рахуємо...' : 'Запустити'}
            </button>
          </div>
        </div>

        {clusters && (
          <div className={styles.clusterGrid}>
            {clusters.clusters.map(c => (
              <div key={c.cluster_id} className={styles.clusterItem}>
                <div className={styles.clusterId}>Кластер {c.cluster_id}</div>
                <div className={styles.clusterSize}>{c.size} точок</div>
                <div className={styles.clusterCoords}>
                  {c.center_lat.toFixed(4)}, {c.center_lng.toFixed(4)}
                </div>
              </div>
            ))}
          </div>
        )}

        {!clusters && (
          <div className={styles.clusterHint}>
            Натисни «Запустити» щоб згрупувати локації по географії
          </div>
        )}
      </div>
    </div>
  )
}