from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers
from .models import Point, Message

class PointSerializer(gis_serializers.GeoFeatureModelSerializer):
    class Meta:
        model = Point
        geo_field = 'location'
        fields = ['id', 'user', 'name', 'description', 'location']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'user', 'point', 'content', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']