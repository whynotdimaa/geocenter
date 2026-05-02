from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from locations.models import Location
from .models import Collection, CollectionMember
from .serializers import (
    CollectionSerializer, CollectionDetailSerializer,
    CollectionMemberSerializer, AddLocationSerializer,
    InviteSerializer, SetMemberRoleSerializer,
)
from .permissions import IsCollectionOwner, IsCollectionOwnerOrEditor

User = get_user_model()


class CollectionViewSet(viewsets.ModelViewSet):
    """
    CRUD для колекцій + кастомні дії.

    list:     GET  /api/geo_collections/                     — мої + публічні
    create:   POST /api/geo_collections/                     — створити
    retrieve: GET  /api/geo_collections/{id}/                — деталі (з локаціями і членами)
    update:   PUT  /api/geo_collections/{id}/                — оновити (тільки власник)
    destroy:  DEL  /api/geo_collections/{id}/                — видалити (тільки власник)

    Кастомні дії:
    POST /api/geo_collections/{id}/add_location/             — додати локацію
    POST /api/geo_collections/{id}/remove_location/          — видалити локацію
    GET  /api/geo_collections/{id}/invite_link/              — отримати посилання-запрошення
    POST /api/geo_collections/join/                          — приєднатись за токеном
    POST /api/geo_collections/{id}/set_role/                 — змінити роль учасника
    DEL  /api/geo_collections/{id}/leave/                    — покинути колекцію
    GET  /api/geo_collections/{id}/export/                   — GeoJSON експорт колекції
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsCollectionOwnerOrEditor)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name', 'description')
    ordering_fields = ('created_at', 'name')

    def get_queryset(self):
        """
        Авторизований бачить: публічні + свої + ті де він член.
        Анонім бачить тільки публічні.
        """
        user = self.request.user
        if user.is_authenticated:
            return Collection.objects.filter(
                is_public=True
            ).union(
                Collection.objects.filter(owner=user)
            ).union(
                Collection.objects.filter(members__user=user)
            ).order_by('-created_at')
        return Collection.objects.filter(is_public=True)

    def get_serializer_class(self):
        """Деталі — повний серіалайзер з локаціями і членами."""
        if self.action == 'retrieve':
            return CollectionDetailSerializer
        return CollectionSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # ------------------------------------------------------------------
    # Управління локаціями в колекції
    # ------------------------------------------------------------------

    @action(detail=True, methods=['post'], url_path='add_location',
            permission_classes=[permissions.IsAuthenticated, IsCollectionOwnerOrEditor])
    def add_location(self, request, pk=None):
        """
        Додати локацію до колекції.
        Body: { "location_id": 42 }
        """
        collection = self.get_object()
        serializer = AddLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        location = get_object_or_404(Location, pk=serializer.validated_data['location_id'])

        # Перевіряємо що локація публічна або належить членові колекції
        if not location.is_public and location.owner != request.user:
            return Response(
                {'error': 'Ця локація приватна і недоступна.'},
                status=status.HTTP_403_FORBIDDEN
            )

        collection.locations.add(location)
        return Response(
            {'detail': f'Локацію "{location.title}" додано до колекції.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='remove_location',
            permission_classes=[permissions.IsAuthenticated, IsCollectionOwnerOrEditor])
    def remove_location(self, request, pk=None):
        """
        Видалити локацію з колекції.
        Body: { "location_id": 42 }
        """
        collection = self.get_object()
        serializer = AddLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        location = get_object_or_404(Location, pk=serializer.validated_data['location_id'])
        collection.locations.remove(location)
        return Response(
            {'detail': f'Локацію "{location.title}" видалено з колекції.'},
            status=status.HTTP_200_OK
        )

    # ------------------------------------------------------------------
    # Запрошення / шерінг
    # ------------------------------------------------------------------

    @action(detail=True, methods=['get'], url_path='invite_link',
            permission_classes=[permissions.IsAuthenticated, IsCollectionOwner])
    def invite_link(self, request, pk=None):
        """
        Повертає унікальне посилання для запрошення в колекцію.
        Доступно тільки власнику.
        GET /api/geo_collections/{id}/invite_link/
        """
        collection = self.get_object()
        invite_url = request.build_absolute_uri(
            f'/api/geo_collections/join/?token={collection.invite_token}'
        )
        return Response({
            'invite_url': invite_url,
            'token': str(collection.invite_token),
        })

    @action(detail=False, methods=['post'], url_path='join',
            permission_classes=[permissions.IsAuthenticated])
    def join(self, request):
        """
        Приєднатись до колекції за токеном-запрошенням.
        Body: { "token": "uuid-токен" }
        POST /api/geo_collections/join/
        """
        serializer = InviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        collection = get_object_or_404(Collection, invite_token=serializer.validated_data['token'])

        if collection.owner == request.user:
            return Response(
                {'detail': 'Ви вже є власником цієї колекції.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        member, created = CollectionMember.objects.get_or_create(
            collection=collection,
            user=request.user,
            defaults={'role': CollectionMember.ROLE_VIEWER}
        )

        if not created:
            return Response(
                {'detail': 'Ви вже є учасником цієї колекції.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'detail': f'Ви приєднались до колекції "{collection.name}" як переглядач.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='set_role',
            permission_classes=[permissions.IsAuthenticated, IsCollectionOwner])
    def set_role(self, request, pk=None):
        """
        Змінити роль учасника. Тільки для власника.
        Body: { "user_id": 5, "role": "editor" }
        POST /api/geo_collections/{id}/set_role/
        """
        collection = self.get_object()
        serializer = SetMemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member = get_object_or_404(
            CollectionMember,
            collection=collection,
            user_id=serializer.validated_data['user_id']
        )
        member.role = serializer.validated_data['role']
        member.save()

        return Response(
            {'detail': f'Роль змінено на "{member.get_role_display()}".'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['delete'], url_path='leave',
            permission_classes=[permissions.IsAuthenticated])
    def leave(self, request, pk=None):
        """
        Покинути колекцію. Власник не може покинути — тільки видалити.
        DELETE /api/geo_collections/{id}/leave/
        """
        collection = self.get_object()

        if collection.owner == request.user:
            return Response(
                {'error': 'Власник не може покинути колекцію. Видаліть її або передайте права.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted, _ = CollectionMember.objects.filter(
            collection=collection, user=request.user
        ).delete()

        if not deleted:
            return Response(
                {'error': 'Ви не є учасником цієї колекції.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'detail': 'Ви покинули колекцію.'},
            status=status.HTTP_204_NO_CONTENT
        )

    # ------------------------------------------------------------------
    # Експорт
    # ------------------------------------------------------------------

    @action(detail=True, methods=['get'], url_path='export',
            permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def export(self, request, pk=None):
        """
        Експортує колекцію як GeoJSON FeatureCollection.
        GET /api/geo_collections/{id}/export/
        """
        from locations.serializers import LocationGeoSerializer

        collection = self.get_object()
        locations = collection.locations.filter(is_public=True)
        geo_serializer = LocationGeoSerializer(locations, many=True)

        return Response({
            'type': 'FeatureCollection',
            'collection': {
                'id': collection.id,
                'name': collection.name,
                'description': collection.description,
            },
            'features': geo_serializer.data.get('features', []),
        })
