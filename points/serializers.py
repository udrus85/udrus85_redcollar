from rest_framework import serializers
from .models import Point, Message

class PointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Point
        fields = ['id', 'user', 'name', 'description', 'latitude', 'longitude']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'user', 'point', 'content', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']