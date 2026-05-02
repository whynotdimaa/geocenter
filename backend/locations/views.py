import json
import csv

from django.http import HttpResponse
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser

from django_filters.rest_framework import DjangoFilterBackend

from .models import Location, Category, Tag
from .serializers import LocationSerializer, LocationGeoSerializer, CategorySerializer, TagSerializer
from .filters import LocationFilter
from .permissions import IsOwnerOrReadOnly


class LocationViewSet(viewsets.ModelViewSet):
    """
    CRUD для локацій + кастомні дії: nearby, bbox, export.

    list:   GET  /api/locations/            — всі публічні + власні
    create: POST /api/locations/            — створити (авторизація обовʼязкова)
    retrieve: GET /api/locations/{id}/      — деталі
    update: PUT  /api/locations/{id}/       — оновити (тільки власник)
    destroy: DEL /api/locations/{id}/       — видалити (тільки власник)
    nearby: GET  /api/locations/nearby/     — в радіусі
    bbox:   GET  /api/locations/bbox/       — в bounding box
    geojson: GET /api/locations/geojson/    — весь список як GeoJSON
    export: GET  /api/locations/export/     — CSV експорт
    """
    serializer_class = LocationSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_class = LocationFilter
    search_fields = ('title', 'description', 'address')
    ordering_fields = ('created_at', 'title')
    ordering = ('-created_at',)

    def get_queryset(self):
        """
        Авторизовані бачать публічні + свої приватні.
        Анонімні бачать тільки публічні.
        """
        user = self.request.user
        if user.is_authenticated:
            return Location.objects.filter(
                is_public=True
            ).union(
                Location.objects.filter(owner=user)
            ).order_by('-created_at')
        return Location.objects.filter(is_public=True)

    def perform_create(self, serializer):
        """Автоматично встановлює власника при створенні."""
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'], url_path='nearby')
    def nearby(self, request):
        """
        Пошук локацій в заданому радіусі.
        Параметри: lat, lng, radius_km (default=5)

        Приклад: /api/locations/nearby/?lat=50.45&lng=30.52&radius_km=10
        """
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
        """
        Пошук локацій у прямокутній зоні (bounding box).
        Параметри: min_lat, min_lng, max_lat, max_lng

        Приклад: /api/locations/bbox/?min_lat=50.0&min_lng=30.0&max_lat=51.0&max_lng=31.0
        """
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

        qs = Location.objects.filter(
            is_public=True,
            point__within_bbox=(min_lng, min_lat, max_lng, max_lat)
        )
        serializer = self.get_serializer(qs, many=True)
        return Response({'count': qs.count(), 'results': serializer.data})

    @action(detail=False, methods=['get'], url_path='geojson')
    def geojson(self, request):
        """
        Повертає всі публічні локації у форматі GeoJSON FeatureCollection.
        Готово для використання в Leaflet / MapBox / QGIS.
        """
        qs = Location.objects.filter(is_public=True)
        serializer = LocationGeoSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """
        Експортує локації поточного користувача в CSV.
        GET /api/locations/export/
        """
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        qs = Location.objects.filter(owner=request.user)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="my_locations.csv"'
        response.write('\ufeff')  # BOM для коректного відкриття в Excel

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
        """
        Імпорт локацій з CSV файлу.
        Очікуваний формат: title,description,latitude,longitude

        POST /api/locations/import/  (multipart, поле: file)
        """
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
    """
    GET /api/locations/categories/      — список категорій
    GET /api/locations/categories/{id}/ — деталі категорії
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (permissions.AllowAny,)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/locations/tags/ — список тегів
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)