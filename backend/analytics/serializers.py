from rest_framework import serializers
from .models import ClusterResult


class UserStatsSerializer(serializers.Serializer):
    """Статистика по поточному користувачу."""
    total_locations = serializers.IntegerField()
    public_locations = serializers.IntegerField()
    private_locations = serializers.IntegerField()
    total_collections = serializers.IntegerField()
    total_views_received = serializers.IntegerField()
    most_viewed_location = serializers.DictField(allow_null=True)
    locations_by_category = serializers.ListField()
    locations_last_30_days = serializers.IntegerField()


class HeatmapPointSerializer(serializers.Serializer):
    """Одна точка для теплової карти."""
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    weight = serializers.FloatField()


class ClusterPointSerializer(serializers.Serializer):
    """Точка всередині кластера."""
    id = serializers.IntegerField()
    title = serializers.CharField()
    lat = serializers.FloatField()
    lng = serializers.FloatField()


class ClusterSerializer(serializers.Serializer):
    """Один кластер з центром і списком точок."""
    cluster_id = serializers.IntegerField()
    center_lat = serializers.FloatField()
    center_lng = serializers.FloatField()
    size = serializers.IntegerField()
    points = ClusterPointSerializer(many=True)


class ClusterResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClusterResult
        fields = ('id', 'n_clusters', 'result_json', 'created_at')
        read_only_fields = ('result_json', 'created_at')


class DistanceSerializer(serializers.Serializer):
    """Відповідь на запит відстані між двома точками."""
    point_a = serializers.DictField()
    point_b = serializers.DictField()
    distance_km = serializers.FloatField()
    distance_m = serializers.FloatField()