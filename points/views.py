from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Point, Message
from .serializers import PointSerializer, MessageSerializer

# Create your views here.

class PointViewSet(viewsets.ModelViewSet):
    queryset = Point.objects.all()
    serializer_class = PointSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        radius = request.query_params.get('radius')
        if not all([lat, lon, radius]):
            return Response({'error': 'lat, lon, radius required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            lat = float(lat)
            lon = float(lon)
            radius = float(radius)
        except ValueError:
            return Response({'error': 'Invalid parameters'}, status=status.HTTP_400_BAD_REQUEST)
        # Approximate distance filter (1 degree ~ 111 km)
        lat_range = radius / 111
        lon_range = radius / (111 * abs(lat) or 1)  # Adjust for latitude
        points = Point.objects.filter(
            latitude__range=(lat - lat_range, lat + lat_range),
            longitude__range=(lon - lon_range, lon + lon_range)
        )
        serializer = self.get_serializer(points, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        radius = request.query_params.get('radius')
        if not all([lat, lon, radius]):
            return Response({'error': 'lat, lon, radius required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            lat = float(lat)
            lon = float(lon)
            radius = float(radius)
        except ValueError:
            return Response({'error': 'Invalid parameters'}, status=status.HTTP_400_BAD_REQUEST)
        # Approximate distance filter
        lat_range = radius / 111
        lon_range = radius / (111 * abs(lat) or 1)
        messages = Message.objects.filter(
            point__latitude__range=(lat - lat_range, lat + lat_range),
            point__longitude__range=(lon - lon_range, lon + lon_range)
        )
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
