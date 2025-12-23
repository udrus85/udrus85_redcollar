from math import atan2, cos, radians, sin, sqrt

from django.contrib.gis.geos import Point as GEOSPoint
from django.contrib.gis.measure import D
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Message, Point
from .serializers import MessageSerializer, PointSerializer


def _parse_geo_params(request):
    lat = request.query_params.get('latitude') or request.query_params.get('lat')
    lon = request.query_params.get('longitude') or request.query_params.get('lon')
    radius = request.query_params.get('radius')
    if not all([lat, lon, radius]):
        return None, None, None, Response({'error': 'latitude, longitude, radius are required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        return float(lat), float(lon), float(radius), None
    except (TypeError, ValueError):
        return None, None, None, Response({'error': 'Invalid geo parameters'}, status=status.HTTP_400_BAD_REQUEST)


def _haversine_km(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * earth_radius_km * atan2(sqrt(a), sqrt(1 - a))


class PointViewSet(viewsets.ModelViewSet):
    queryset = Point.objects.all()
    serializer_class = PointSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        lat, lon, radius, error_response = _parse_geo_params(request)
        if error_response:
            return error_response

        try:
            center = GEOSPoint(lon, lat, srid=4326)
            qs = Point.objects.filter(location__distance_lte=(center, D(km=radius)))
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        except Exception:
            points = [p for p in Point.objects.all() if _haversine_km(lat, lon, p.latitude, p.longitude) <= radius]
            serializer = self.get_serializer(points, many=True)
            return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.select_related('point', 'user')
    serializer_class = MessageSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        lat, lon, radius, error_response = _parse_geo_params(request)
        if error_response:
            return error_response

        try:
            center = GEOSPoint(lon, lat, srid=4326)
            qs = Message.objects.select_related('point').filter(point__location__distance_lte=(center, D(km=radius)))
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        except Exception:
            messages = [m for m in Message.objects.select_related('point') if _haversine_km(lat, lon, m.point.latitude, m.point.longitude) <= radius]
            serializer = self.get_serializer(messages, many=True)
            return Response(serializer.data)
