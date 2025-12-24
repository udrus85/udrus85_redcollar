from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from django.contrib.gis.geos import Point as GEOSPoint
from .models import Point, Message

class PointSerializer(serializers.ModelSerializer):
    location = GeometryField(required=False, allow_null=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    
    class Meta:
        model = Point
        fields = ['id', 'user', 'name', 'description', 'latitude', 'longitude', 'location']
        read_only_fields = ['id', 'user']

    def validate_latitude(self, value):
        if value is not None and not (-90 <= value <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if value is not None and not (-180 <= value <= 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value

    def validate(self, data):
        location = data.get('location')
        lat = data.get('latitude')
        lon = data.get('longitude')
        if not location and (lat is None or lon is None):
            raise serializers.ValidationError("Either 'location' or both 'latitude' and 'longitude' must be provided.")
        return data

    def create(self, validated_data):
        location = validated_data.get('location')
        lat = validated_data.get('latitude')
        lon = validated_data.get('longitude')
        
        if location:
            validated_data['latitude'] = location.y
            validated_data['longitude'] = location.x
        elif lat is not None and lon is not None:
            validated_data['location'] = GEOSPoint(lon, lat, srid=4326)
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        location = validated_data.get('location')
        lat = validated_data.get('latitude')
        lon = validated_data.get('longitude')
        
        if location:
            validated_data['latitude'] = location.y
            validated_data['longitude'] = location.x
        elif lat is not None and lon is not None:
            validated_data['location'] = GEOSPoint(lon, lat, srid=4326)
        
        return super().update(instance, validated_data)

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'user', 'point', 'content', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']