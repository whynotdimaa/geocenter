from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import NewsPoint

class NewsPointSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = NewsPoint
        geo_field = "location"
        fields = ("id", "title", "content", "created_at")
