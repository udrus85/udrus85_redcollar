"""
Конфигурация URL для проекта geopoints.

Список `urlpatterns` направляет URL на views. Для получения дополнительной информации см.:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Примеры:
Function views (представления-функции)
    1. Добавьте импорт:  from my_app import views
    2. Добавьте URL в urlpatterns:  path('', views.home, name='home')
Class-based views (представления на основе классов)
    1. Добавьте импорт:  from other_app.views import Home
    2. Добавьте URL в urlpatterns:  path('', Home.as_view(), name='home')
Включение другого URLconf
    1. Импортируйте функцию include(): from django.urls import include, path
    2. Добавьте URL в urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('points.urls')),
    path('api/auth/token/', obtain_auth_token, name='api-token'),
]
