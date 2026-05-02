from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, RegisterSerializer, ChangePasswordSerializer
)

User = get_user_model()


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Приймає email + password, повертає access та refresh JWT токени.
    """
    pass


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Реєстрація нового користувача. Не потребує авторизації.
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Додає refresh токен до чорного списку (blacklist).
    Потребує: { "refresh": "<token>" }
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh токен обовʼязковий.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Вихід виконано успішно.'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MeView(generics.RetrieveAPIView):
    """
    GET /api/auth/me/
    Повертає дані поточного авторизованого користувача разом з профілем.
    """
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/profile/  — отримати профіль
    PUT  /api/auth/profile/  — оновити username, avatar, bio + налаштування профілю
    PATCH /api/auth/profile/ — часткове оновлення
    """
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    Потребує: { "old_password", "new_password", "new_password2" }
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Невірний поточний пароль.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'detail': 'Пароль змінено успішно.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)