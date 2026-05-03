from django.urls import path
from .views import StatsView, HeatmapView, ClusterView, DistanceView

urlpatterns = [
    # GET  /api/analytics/stats/      — статистика по юзеру
    path('stats/', StatsView.as_view(), name='analytics_stats'),

    # GET  /api/analytics/heatmap/    — дані для теплової карти
    path('heatmap/', HeatmapView.as_view(), name='analytics_heatmap'),

    # POST /api/analytics/cluster/    — K-Means кластеризація
    path('cluster/', ClusterView.as_view(), name='analytics_cluster'),

    # GET  /api/analytics/distance/   — відстань між двома точками
    path('distance/', DistanceView.as_view(), name='analytics_distance'),
]