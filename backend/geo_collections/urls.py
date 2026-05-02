from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CollectionViewSet

router = DefaultRouter()
router.register(r'', CollectionViewSet, basename='collection')

urlpatterns = [
    path('', include(router.urls)),
]

# Автоматично генеровані маршрути:
# GET    /api/geo_collections/                        — список
# POST   /api/geo_collections/                        — створити
# GET    /api/geo_collections/{id}/                   — деталі (з локаціями і членами)
# PUT    /api/geo_collections/{id}/                   — оновити
# PATCH  /api/geo_collections/{id}/                   — часткове оновлення
# DELETE /api/geo_collections/{id}/                   — видалити
# POST   /api/geo_collections/{id}/add_location/      — додати локацію
# POST   /api/geo_collections/{id}/remove_location/   — видалити локацію
# GET    /api/geo_collections/{id}/invite_link/       — посилання-запрошення
# POST   /api/geo_collections/join/                   — приєднатись за токеном
# POST   /api/geo_collections/{id}/set_role/          — змінити роль учасника
# DELETE /api/geo_collections/{id}/leave/             — покинути колекцію
# GET    /api/geo_collections/{id}/export/            — GeoJSON експорт
