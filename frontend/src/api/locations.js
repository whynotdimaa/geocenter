import api from './axios'

export const locationsApi = {
  // Список локацій (з фільтрами)
  list: (params, signal) => api.get('/locations/', { params, signal }),

  // Деталі однієї локації
  get: (id) => api.get(`/locations/${id}/`),

  // Створити
  create: (data) => api.post('/locations/', data),

  // Оновити
  update: (id, data) => api.put(`/locations/${id}/`, data),

  // Частково оновити
  patch: (id, data) => api.patch(`/locations/${id}/`, data),

  // Видалити
  remove: (id) => api.delete(`/locations/${id}/`),

  // Пошук в радіусі
  nearby: (lat, lng, radius_km = 5) =>
    api.get('/locations/nearby/', { params: { lat, lng, radius_km } }),

  // GeoJSON всіх публічних
  geojson: () => api.get('/locations/geojson/'),

  // CSV експорт (повертає blob)
  exportCsv: () =>
    api.get('/locations/export/', { responseType: 'blob' }),

  // Категорії
  categories: () => api.get('/locations/categories/'),

  // Теги
  tags: () => api.get('/locations/tags/'),

  // Reverse geocoding через Nominatim (OpenStreetMap)
  reverseGeocode: async (lat, lng) => {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1&accept-language=uk`
    const response = await fetch(url, {
      headers: { 'User-Agent': 'GeoCenter/1.0' }
    })
    if (!response.ok) throw new Error('Geocoding failed')
    return response.json()
  },

  // Коментарі до локації
  getComments: (locationId) => api.get(`/locations/${locationId}/comments/`),
  addComment: (locationId, text) => api.post(`/locations/${locationId}/comments/`, { text }),
  deleteComment: (locationId, commentId) => api.delete(`/locations/${locationId}/comments/${commentId}/`),
}

export const analyticsApi = {
  stats: () => api.get('/analytics/stats/'),
  heatmap: (params) => api.get('/analytics/heatmap/', { params }),
  cluster: (n_clusters) => api.post('/analytics/cluster/', { n_clusters }),
  distance: (lat1, lng1, lat2, lng2) =>
    api.get('/analytics/distance/', { params: { lat1, lng1, lat2, lng2 } }),
}

export const collectionsApi = {
  list: () => api.get('/collections/'),
  get: (id) => api.get(`/collections/${id}/`),
  create: (data) => api.post('/collections/', data),
  update: (id, data) => api.put(`/collections/${id}/`, data),
  remove: (id) => api.delete(`/collections/${id}/`),
  addLocation: (id, location_id) =>
    api.post(`/collections/${id}/add_location/`, { location_id }),
  removeLocation: (id, location_id) =>
    api.post(`/collections/${id}/remove_location/`, { location_id }),
  inviteLink: (id) => api.get(`/collections/${id}/invite_link/`),
  join: (token) => api.post('/collections/join/', { token }),
  export: (id) => api.get(`/collections/${id}/export/`),
}
