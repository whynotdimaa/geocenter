from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import Point
from .models import Location, Category, Tag, LocationComment


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'color', 'icon')


class LocationSerializer(serializers.ModelSerializer):
    """
    Стандартний серіалайзер — повертає latitude/longitude як окремі поля.
    Зручний для таблиць і форм.
    """
    owner = serializers.StringRelatedField(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tags', many=True, write_only=True, required=False
    )

    # Повертаємо lat/lng окремо для зручності
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = (
            'id', 'title', 'description',
            'latitude', 'longitude', 'lat', 'lng',
            'owner', 'category', 'category_id',
            'tags', 'tag_ids',
            'is_public', 'address', 'altitude', 'image',
            'created_at', 'updated_at',
        )
        read_only_fields = ('owner', 'created_at', 'updated_at')

    def get_lat(self, obj):
        return obj.point.y

    def get_lng(self, obj):
        return obj.point.x

    def create(self, validated_data):
        lat = validated_data.pop('latitude')
        lng = validated_data.pop('longitude')
        tags = validated_data.pop('tags', [])
        validated_data['point'] = Point(lng, lat, srid=4326)
        location = Location.objects.create(**validated_data)
        location.tags.set(tags)
        return location

    def update(self, instance, validated_data):
        lat = validated_data.pop('latitude', None)
        lng = validated_data.pop('longitude', None)
        tags = validated_data.pop('tags', None)

        if lat is not None and lng is not None:
            instance.point = Point(lng, lat, srid=4326)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)
        return instance


class LocationGeoSerializer(GeoFeatureModelSerializer):
    """
    GeoJSON серіалайзер — повертає стандартний GeoJSON FeatureCollection.
    Використовується для експорту та відображення на карті (Leaflet/MapBox).
    """
    owner = serializers.StringRelatedField(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Location
        geo_field = 'point'
        fields = ('id', 'title', 'description', 'owner', 'tags', 'category', 'is_public', 'address', 'created_at', 'point')


class LocationCommentSerializer(serializers.ModelSerializer):
    """Серіалайзер для коментарів до локації."""
    user = serializers.StringRelatedField(read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = LocationComment
        fields = ('id', 'text', 'user', 'user_id', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'user_id', 'created_at', 'updated_at')