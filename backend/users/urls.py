from django.urls import path

urlpatterns = [
    # Всі auth-ендпоінти перенесені до FastAPI auth_service.
    # Django-бекенд (locations_service) використовує RemoteJWTAuthentication
    # для верифікації токенів через http://auth_service:8001/api/auth/verify
]
