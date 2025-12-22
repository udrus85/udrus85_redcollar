from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MessageViewSet, PointViewSet

router = DefaultRouter()
router.register(r'points', PointViewSet, basename='points')

urlpatterns = [
    path('points/messages/', MessageViewSet.as_view({'get': 'list', 'post': 'create'}), name='messages-list'),
    path('points/messages/search/', MessageViewSet.as_view({'get': 'search'}), name='messages-search'),
    path('', include(router.urls)),
]