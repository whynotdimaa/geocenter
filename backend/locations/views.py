import json
import csv

from django.http import HttpResponse
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Location, Category, Tag, LocationComment
from .serializers import LocationSerializer, LocationGeoSerializer, CategorySerializer, TagSerializer, LocationCommentSerializer
from .filters import LocationFilter
from .permissions import IsOwnerOrReadOnly

from analytics.views import TrackViewMixin


class LocationViewSet(TrackViewMixin, viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_class = LocationFilter
    search_fields = ('title', 'description', 'address')
    ordering_fields = ('created_at', 'title')
    ordering = ('-created_at',)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return (
                Location.objects
                .filter(Q(is_public=True) | Q(owner=user))
                .select_related('owner', 'category')
                .prefetch_related('tags')
                .order_by('-created_at')
            )
        return (
            Location.objects
            .filter(is_public=True)
            .select_related('owner', 'category')
            .prefetch_related('tags')
            .order_by('-created_at')
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.track(request, instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='nearby')
    def nearby(self, request):
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
            radius_km = float(request.query_params.get('radius_km', 5))
        except (TypeError, ValueError):
            return Response(
                {'error': 'Вкажіть коректні параметри: lat, lng, radius_km'},
                status=status.HTTP_400_BAD_REQUEST
            )

        center = Point(lng, lat, srid=4326)
        qs = Location.objects.filter(
            is_public=True,
            point__distance_lte=(center, D(km=radius_km))
        ).annotate(
            distance=Distance('point', center)
        ).order_by('distance')

        serializer = self.get_serializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'center': {'lat': lat, 'lng': lng},
            'radius_km': radius_km,
            'results': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='bbox')
    def bbox(self, request):
        try:
            min_lat = float(request.query_params['min_lat'])
            min_lng = float(request.query_params['min_lng'])
            max_lat = float(request.query_params['max_lat'])
            max_lng = float(request.query_params['max_lng'])
        except (KeyError, ValueError):
            return Response(
                {'error': 'Вкажіть параметри: min_lat, min_lng, max_lat, max_lng'},
                status=status.HTTP_400_BAD_REQUEST
            )

        bbox_poly = Polygon.from_bbox((min_lng, min_lat, max_lng, max_lat))
        qs = Location.objects.filter(
            is_public=True,
            point__within=bbox_poly
        ).select_related('owner', 'category').prefetch_related('tags')

        serializer = self.get_serializer(qs, many=True)
        return Response({'count': qs.count(), 'results': serializer.data})

    @action(
        detail=False, methods=['get'], url_path='geojson',
        permission_classes=[permissions.AllowAny]  # публічний — для analytics_service і фронту
    )
    @method_decorator(cache_page(60 * 5))  # 5 хвилин кеш для GeoJSON
    def geojson(self, request):
        """Повертає GeoJSON FeatureCollection публічних локацій."""
        locations = Location.objects.filter(is_public=True).select_related('category').prefetch_related('tags')
        serializer = LocationGeoSerializer(locations, many=True)
        return Response(serializer.data)

    def _clear_locations_cache(self):
        """Очищує кеш списку локацій та GeoJSON."""
        cache.delete_pattern('*:geocenter:locations_*')
        cache.delete_pattern('*:geocenter:*:geojson_*')

    def perform_update(self, serializer):
        serializer.save()
        self._clear_locations_cache()

    def perform_destroy(self, instance):
        instance.soft_delete()
        self._clear_locations_cache()

    @action(detail=True, methods=['post'], url_path='restore',
            permission_classes=[permissions.IsAuthenticated])
    def restore(self, request, pk=None):
        """Відновлення soft-deleted локації."""
        location = Location.all_objects.get(pk=pk, is_deleted=True)
        if location.owner != request.user:
            return Response(
                {'error': 'Тільки власник може відновити локацію'},
                status=status.HTTP_403_FORBIDDEN
            )
        location.restore()
        self._clear_locations_cache()
        return Response({'message': 'Локацію відновлено'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='trash',
            permission_classes=[permissions.IsAuthenticated])
    def trash(self, request):
        """Список видалених локацій поточного користувача."""
        deleted = Location.all_objects.filter(
            owner=request.user,
            is_deleted=True
        ).order_by('-deleted_at')
        serializer = self.get_serializer(deleted, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        qs = Location.objects.filter(owner=request.user)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="my_locations.csv"'
        response.write('\ufeff')

        writer = csv.writer(response)
        writer.writerow(['ID', 'Назва', 'Опис', 'Широта', 'Довгота', 'Висота', 'Адреса', 'Публічна', 'Категорія', 'Створено'])
        for loc in qs:
            writer.writerow([
                loc.id, loc.title, loc.description,
                loc.point.y, loc.point.x, loc.altitude or '',
                loc.address, loc.is_public,
                loc.category.name if loc.category else '',
                loc.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        return response

    @action(detail=False, methods=['post'], url_path='import',
            permission_classes=[permissions.IsAuthenticated],
            parser_classes=[MultiPartParser])
    def import_csv(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'Файл не надано.'}, status=status.HTTP_400_BAD_REQUEST)

        decoded = file.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded)

        created, errors = [], []
        required_fields = {'title', 'latitude', 'longitude'}

        for i, row in enumerate(reader, start=2):
            if not required_fields.issubset(row.keys()):
                return Response(
                    {'error': f'CSV повинен містити колонки: {", ".join(required_fields)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                loc = Location.objects.create(
                    title=row['title'],
                    description=row.get('description', ''),
                    point=Point(float(row['longitude']), float(row['latitude']), srid=4326),
                    owner=request.user,
                    is_public=row.get('is_public', 'true').lower() == 'true'
                )
                created.append(loc.id)
            except Exception as e:
                errors.append({'row': i, 'error': str(e)})

        return Response({
            'created': len(created),
            'errors': errors
        }, status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (permissions.AllowAny,)

    @method_decorator(cache_page(60 * 15))  # 15 хвилин кеш
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)

    @method_decorator(cache_page(60 * 15))  # 15 хвилин кеш
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class LocationCommentViewSet(viewsets.ModelViewSet):
    """API для коментарів до локацій."""
    serializer_class = LocationCommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return LocationComment.objects.filter(location_id=self.kwargs['location_pk'])

    def perform_create(self, serializer):
        location = get_object_or_404(Location, pk=self.kwargs['location_pk'])
        serializer.save(user=self.request.user, location=location)