"""
Конфигурация WSGI для проекта geopoints.

Предоставляет WSGI callable как переменную уровня модуля с именем ``application``.

Для получения дополнительной информации об этом файле см.:
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geopoints.settings')

application = get_wsgi_application()
