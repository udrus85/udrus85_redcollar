"""
Конфигурация ASGI для проекта geopoints.

Предоставляет ASGI callable как переменную уровня модуля с именем ``application``.

Для получения дополнительной информации об этом файле см.:
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geopoints.settings')

application = get_asgi_application()
