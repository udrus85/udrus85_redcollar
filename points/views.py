from math import atan2, cos, radians, sin, sqrt
import logging

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point as GEOSPoint
from django.contrib.gis.geos.error import GEOSException
from django.contrib.gis.measure import D
from django.db.utils import OperationalError, ProgrammingError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Message, Point
from .serializers import MessageSerializer, PointSerializer

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Стандартная пагинация для API."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def _parse_geo_params(request):
    """
    Парсинг и валидация географических параметров из запроса.
    
    Args:
        request: HTTP запрос с параметрами latitude/lat, longitude/lon, radius
        
    Returns:
        tuple: (lat, lon, radius, error_response) где error_response None если нет ошибок
    """
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
        # Валидация координат
        if not (-90 <= lat <= 90):
            return None, None, None, Response({'error': 'Широта должна быть в диапазоне от -90 до 90'}, status=status.HTTP_400_BAD_REQUEST)
        if not (-180 <= lon <= 180):
            return None, None, None, Response({'error': 'Долгота должна быть в диапазоне от -180 до 180'}, status=status.HTTP_400_BAD_REQUEST)
        return lat, lon, radius, None
    except (TypeError, ValueError):
        return None, None, None, Response({'error': 'Некорректные географические параметры'}, status=status.HTTP_400_BAD_REQUEST)


def _haversine_km(lat1, lon1, lat2, lon2):
    """
    Вычисление расстояния между двумя точками по формуле Haversine.
    
    Args:
        lat1, lon1: Координаты первой точки (градусы)
        lat2, lon2: Координаты второй точки (градусы)
        
    Returns:
        float: Расстояние в километрах
    """
    earth_radius_km = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * earth_radius_km * atan2(sqrt(a), sqrt(1 - a))


class PointViewSet(viewsets.ModelViewSet):
    """ViewSet для управления географическими точками."""
    queryset = Point.objects.all()
    serializer_class = PointSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Поиск точек в заданном радиусе от координат.
        
        Query параметры:
            latitude/lat: Широта центральной точки
            longitude/lon: Долгота центральной точки
            radius: Радиус поиска в километрах (0-1000)
        """
        lat, lon, radius, error_response = _parse_geo_params(request)
        if error_response:
            return error_response

        try:
            center = GEOSPoint(lon, lat, srid=4326)
            # Поиск с сортировкой по расстоянию
            qs = Point.objects.filter(location__distance_lte=(center, D(km=radius)))
            qs = qs.annotate(distance=Distance('location', center)).order_by('distance')
            
            # Применяем пагинацию
            page = self.paginate_queryset(qs)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        except (OperationalError, ProgrammingError, GEOSException) as e:
            # Fallback на Haversine (без PostGIS или для SQLite)
            logger.warning(f"PostGIS query failed, falling back to Haversine: {e}")
            # Ограничиваем только точками с координатами
            points = [
                p for p in Point.objects.exclude(latitude__isnull=True, longitude__isnull=True)
                if _haversine_km(lat, lon, p.latitude, p.longitude) <= radius
            ]
            
            # Применяем пагинацию к списку
            page = self.paginate_queryset(points)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(points, many=True)
            return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet для управления сообщениями, привязанными к точкам."""
    queryset = Message.objects.select_related('point', 'user')
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Поиск сообщений по точкам в заданном радиусе от координат.
        
        Query параметры:
            latitude/lat: Широта центральной точки
            longitude/lon: Долгота центральной точки
            radius: Радиус поиска в километрах (0-1000)
        """
        lat, lon, radius, error_response = _parse_geo_params(request)
        if error_response:
            return error_response

        try:
            center = GEOSPoint(lon, lat, srid=4326)
            # Поиск с сортировкой по расстоянию точки
            qs = Message.objects.select_related('point').filter(point__location__distance_lte=(center, D(km=radius)))
            qs = qs.annotate(distance=Distance('point__location', center)).order_by('distance')
            
            # Применяем пагинацию
            page = self.paginate_queryset(qs)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        except (OperationalError, ProgrammingError, GEOSException) as e:
            # Fallback на Haversine
            logger.warning(f"PostGIS query failed, falling back to Haversine: {e}")
            messages = [
                m for m in Message.objects.select_related('point').exclude(point__latitude__isnull=True, point__longitude__isnull=True)
                if _haversine_km(lat, lon, m.point.latitude, m.point.longitude) <= radius
            ]
            
            # Применяем пагинацию к списку
            page = self.paginate_queryset(messages)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(messages, many=True)
            return Response(serializer.data)
