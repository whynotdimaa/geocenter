import requests
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User


AUTH_SERVICE_URL = getattr(settings, 'AUTH_SERVICE_URL', 'http://auth_service:8001')


class RemoteJWTAuthentication(BaseAuthentication):
    """
    Кастомний бекенд автентифікації для Django.
    Замість локальної перевірки JWT — надсилає токен до auth_service (FastAPI)
    і отримує дані користувача. Якщо юзер не існує в Django-БД — створює його.
    Це дозволяє Django-сервісам (locations, collections) використовувати токени,
    видані FastAPI auth_service, без спільного секретного ключа.
    """

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None  # Анонімний доступ

        token = auth_header.split(' ', 1)[1].strip()
        if not token:
            return None

        try:
            response = requests.post(
                f'{AUTH_SERVICE_URL}/api/auth/verify',
                json={'token': token},
                timeout=5,
            )
        except requests.RequestException:
            raise AuthenticationFailed('Auth service недоступний')

        if response.status_code != 200:
            raise AuthenticationFailed('Невалідний або прострочений токен')

        data = response.json()
        email = data.get('email', '').strip()
        username = data.get('username', '').strip()

        if not email:
            raise AuthenticationFailed('Auth service повернув некоректні дані')

        # Отримуємо або створюємо юзера в локальній Django-БД (шукаємо по email)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username or email.split('@')[0],
            },
        )

        # Синхронізуємо username якщо змінився
        if not created and username and user.username != username:
            user.username = username
            user.save(update_fields=['username'])

        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer'
