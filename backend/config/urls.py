from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Адмін панель
    path('admin/', admin.site.urls),

    # Auth — реєстрація, логін, логаут, профіль
    path('api/auth/', include('users.urls')),

    # Локації — головна функціональність
    path('api/locations/', include('locations.urls')),

    # OpenAPI схема (JSON)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI — інтерактивна документація
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ReDoc — альтернативна документація
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)