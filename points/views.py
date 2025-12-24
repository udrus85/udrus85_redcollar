from math import atan2, cos, radians, sin, sqrt

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point as GEOSPoint
from django.contrib.gis.measure import D
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Message, Point
from .serializers import MessageSerializer, PointSerializer


def _parse_geo_params(request):
    lat = request.query_params.get('latitude') or request.query_params.get('lat')
    lon = request.query_params.get('longitude') or request.query_params.get('lon')
    radius = request.query_params.get('radius')
    if not all([lat, lon, radius]):
        return None, None, None, Response({'error': 'Требуются параметры latitude, longitude и radius'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        lat, lon, radius = float(lat), float(lon), float(radius)
        # Валидация радиуса
        if radius <= 0 or radius > 1000:
            return None, None, None, Response({'error': 'Радиус должен быть в диапазоне от 0 до 1000 км'}, status=status.HTTP_400_BAD_REQUEST)
        return lat, lon, radius, None
    except (TypeError, ValueError):
        return None, None, None, Response({'error': 'Некорректные географические параметры'}, status=status.HTTP_400_BAD_REQUEST)


def _haversine_km(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * earth_radius_km * atan2(sqrt(a), sqrt(1 - a))


class PointViewSet(viewsets.ModelViewSet):
    queryset = Point.objects.all()
    serializer_class = PointSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        lat, lon, radius, error_response = _parse_geo_params(request)
        if error_response:
            return error_response

        try:
            center = GEOSPoint(lon, lat, srid=4326)
            # Поиск с сортировкой по расстоянию
            qs = Point.objects.filter(location__distance_lte=(center, D(km=radius)))
            qs = qs.annotate(distance=Distance('location', center)).order_by('distance')
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        except Exception as e:
            # Fallback на Haversine (без PostGIS или для SQLite)
            # Ограничиваем только точками с координатами
            points = [
                p for p in Point.objects.exclude(latitude__isnull=True, longitude__isnull=True)
                if _haversine_km(lat, lon, p.latitude, p.longitude) <= radius
            ]
            serializer = self.get_serializer(points, many=True)
            return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.select_related('point', 'user')
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        lat, lon, radius, error_response = _parse_geo_params(request)
        if error_response:
            return error_response

        try:
            center = GEOSPoint(lon, lat, srid=4326)
            # Поиск с сортировкой по расстоянию точки
            qs = Message.objects.select_related('point').filter(point__location__distance_lte=(center, D(km=radius)))
            qs = qs.annotate(distance=Distance('point__location', center)).order_by('distance')
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        except Exception as e:
            # Fallback на Haversine
            messages = [
                m for m in Message.objects.select_related('point').exclude(point__latitude__isnull=True, point__longitude__isnull=True)
                if _haversine_km(lat, lon, m.point.latitude, m.point.longitude) <= radius
            ]
            serializer = self.get_serializer(messages, many=True)
            return Response(serializer.data)
