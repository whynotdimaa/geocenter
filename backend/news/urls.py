from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsPointViewSet

router = DefaultRouter()
router.register(r'points', NewsPointViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
