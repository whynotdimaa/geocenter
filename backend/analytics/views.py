from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.utils import timezone
from datetime import timedelta

from locations.models import Location
from .models import LocationView, ClusterResult
from .serializers import (
    UserStatsSerializer, HeatmapPointSerializer,
    ClusterSerializer, DistanceSerializer,
)
from django.contrib.gis.geos import Polygon
from django.db.models import Count
User = get_user_model()


class StatsView(APIView):
    """
    GET /api/analytics/stats/
    Повертає статистику по поточному авторизованому користувачу:
    загальна кількість локацій, колекцій, переглядів, найпопулярніша локація тощо.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        locations = Location.objects.filter(owner=user)
        last_30 = timezone.now() - timedelta(days=30)

        # Найпопулярніша за кількістю переглядів — правильна логіка
        most_viewed = None
        top = (
            locations
            .annotate(view_count=Count('views'))
            .order_by('-view_count')
            .first()
        )
        if top:
            most_viewed = {
                'id': top.id,
                'title': top.title,
                'views': top.view_count,
            }

        by_category = (
            locations
            .values('category__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        data = {
            'total_locations': locations.count(),
            'public_locations': locations.filter(is_public=True).count(),
            'private_locations': locations.filter(is_public=False).count(),
            'total_collections': user.collections.count(),
            'total_views_received': LocationView.objects.filter(location__owner=user).count(),
            'most_viewed_location': most_viewed,
            'locations_by_category': list(by_category),
            'locations_last_30_days': locations.filter(created_at__gte=last_30).count(),
        }

        serializer = UserStatsSerializer(data)
        return Response(serializer.data)


class HeatmapView(APIView):
    """
    GET /api/analytics/heatmap/
    Повертає список точок з вагою для побудови теплової карти.
    Вага = кількість переглядів локації (мін. 1).

    Опціональні параметри:
    - bbox: min_lat,min_lng,max_lat,max_lng  — обмежити зону
    - category: id категорії
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        from django.db.models import Count

        qs = Location.objects.filter(is_public=True).annotate(
            view_count=Count('views')
        )

        # Фільтр по bbox якщо переданий
        bbox = request.query_params.get('bbox')
        if bbox:
            try:
                min_lat, min_lng, max_lat, max_lng = map(float, bbox.split(','))
                bbox_poly = Polygon.from_bbox((min_lng, min_lat, max_lng, max_lat))
                qs = qs.filter(point__within=bbox_poly)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'bbox має бути у форматі: min_lat,min_lng,max_lat,max_lng'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Фільтр по категорії
        category_id = request.query_params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)

        points = [
            {
                'lat': loc.point.y,
                'lng': loc.point.x,
                'weight': max(loc.view_count, 1),
            }
            for loc in qs
        ]

        return Response({
            'count': len(points),
            'points': points,
        })


class ClusterView(APIView):
    """
    POST /api/analytics/cluster/
    Кластеризує публічні локації методом K-Means.
    Повертає центри кластерів і точки що до них входять.

    Body: { "n_clusters": 5 }   (default: 5, max: 20)

    Потребує: pip install scikit-learn
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            import numpy as np
            from sklearn.cluster import KMeans
        except ImportError:
            return Response(
                {'error': 'scikit-learn не встановлений. Виконай: pip install scikit-learn'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Кількість кластерів
        try:
            n_clusters = int(request.data.get('n_clusters', 5))
            if not 2 <= n_clusters <= 20:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'n_clusters має бути числом від 2 до 20.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        locations = list(
            Location.objects.filter(is_public=True).select_related('category')
        )

        if len(locations) < n_clusters:
            return Response(
                {'error': f'Недостатньо точок для {n_clusters} кластерів. Є лише {len(locations)}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Масив координат [lng, lat]
        coords = np.array([[loc.point.x, loc.point.y] for loc in locations])

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(coords)

        # Формуємо результат
        clusters = []
        for i in range(n_clusters):
            indices = np.where(labels == i)[0]
            center = kmeans.cluster_centers_[i]
            cluster_points = [
                {
                    'id': locations[j].id,
                    'title': locations[j].title,
                    'lat': locations[j].point.y,
                    'lng': locations[j].point.x,
                }
                for j in indices
            ]
            clusters.append({
                'cluster_id': i,
                'center_lat': round(center[1], 6),
                'center_lng': round(center[0], 6),
                'size': len(indices),
                'points': cluster_points,
            })

        # Зберігаємо результат в БД
        ClusterResult.objects.create(
            user=request.user,
            n_clusters=n_clusters,
            result_json=clusters,
        )

        return Response({
            'n_clusters': n_clusters,
            'total_points': len(locations),
            'clusters': clusters,
        })


class DistanceView(APIView):
    """
    GET /api/analytics/distance/
    Обраховує відстань між двома точками (геодезична, по поверхні Землі).

    Параметри:
    - lat1, lng1  — перша точка
    - lat2, lng2  — друга точка

    Приклад: /api/analytics/distance/?lat1=50.45&lng1=30.52&lat2=49.84&lng2=24.03
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        try:
            lat1 = float(request.query_params['lat1'])
            lng1 = float(request.query_params['lng1'])
            lat2 = float(request.query_params['lat2'])
            lng2 = float(request.query_params['lng2'])
        except (KeyError, ValueError, TypeError):
            return Response(
                {'error': 'Вкажіть параметри: lat1, lng1, lat2, lng2'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from geopy.distance import geodesic
            distance = geodesic((lat1, lng1), (lat2, lng2))
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'point_a': {'lat': lat1, 'lng': lng1},
            'point_b': {'lat': lat2, 'lng': lng2},
            'distance_km': round(distance.km, 4),
            'distance_m': round(distance.m, 2),
        })


class TrackViewMixin:
    """
    Міксін для автоматичного логування перегляду локації.
    Підключається в LocationViewSet.retrieve() якщо потрібно.
    """
    @staticmethod
    def track(request, location):
        ip = request.META.get('REMOTE_ADDR')
        user = request.user if request.user.is_authenticated else None
        LocationView.objects.create(location=location, user=user, ip_address=ip)