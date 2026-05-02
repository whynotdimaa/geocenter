from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocationViewSet, CategoryViewSet, TagViewSet

router = DefaultRouter()
router.register(r'', LocationViewSet, basename='location')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]

# Автоматично генеровані маршрути:
# GET    /api/locations/                  — список
# POST   /api/locations/                  — створити
# GET    /api/locations/{id}/             — деталі
# PUT    /api/locations/{id}/             — оновити
# PATCH  /api/locations/{id}/             — часткове оновлення
# DELETE /api/locations/{id}/             — видалити
# GET    /api/locations/nearby/           — в радіусі
# GET    /api/locations/bbox/             — bounding box пошук
# GET    /api/locations/geojson/          — GeoJSON експорт
# GET    /api/locations/export/           — CSV експорт
# POST   /api/locations/import/           — CSV імпорт
# GET    /api/locations/categories/       — категорії
# GET    /api/locations/tags/             — теги