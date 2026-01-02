"""
Настройки Django для проекта geopoints.

Сгенерировано командой 'django-admin startproject' с использованием Django 6.0.

Для получения дополнительной информации об этом файле см.:
https://docs.djangoproject.com/en/6.0/topics/settings/

Для получения полного списка настроек и их значений см.:
https://docs.djangoproject.com/en/6.0/ref/settings/
"""

from pathlib import Path
import os

# Убедиться, что Windows может найти GDAL/GEOS/PROJ DLL (Python 3.8+ требует явного указания директорий DLL)
if os.name == 'nt':
    dll_dirs = []
    osgeo_root = os.environ.get('OSGEO4W_ROOT')
    if osgeo_root:
        dll_dirs.append(Path(osgeo_root) / 'bin')
    gdal_path = os.environ.get('GDAL_LIBRARY_PATH')
    if gdal_path:
        dll_dirs.append(Path(gdal_path).parent)
    geos_path = os.environ.get('GEOS_LIBRARY_PATH')
    if geos_path:
        dll_dirs.append(Path(geos_path).parent)
    for d in dll_dirs:
        if d and d.exists():
            try:
                os.add_dll_directory(str(d))
            except Exception:
                pass

# Создание путей внутри проекта следующим образом: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Настройки для быстрого запуска разработки - не подходит для продакшена
# См. https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ: держите секретный ключ, используемый в продакшене, в секрете!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-r+kw@_=j@)_w!$(2n62#q=w@!!tk8ov!j6(9b_5)@7kl5gtd+l')

# ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ: не запускайте с включённым режимом отладки в продакшене!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')


# Определение приложения

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'rest_framework',
    'rest_framework.authtoken',
    'points',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'geopoints.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'geopoints.wsgi.application'


# База данных
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

USE_POSTGIS = os.environ.get('USE_POSTGIS', '1') == '1'  # по умолчанию PostGIS, если переменная окружения присутствует

if USE_POSTGIS and os.environ.get('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER', ''),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    # Резервный вариант для локальной разработки без PostGIS (ограниченная функциональность)
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.spatialite',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Валидация паролей
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Интернационализация
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Статические файлы (CSS, JavaScript, изображения)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Опционально: установите эти переменные через окружение при использовании OSGeo4W/Conda на Windows
GDAL_LIBRARY_PATH = os.environ.get('GDAL_LIBRARY_PATH')
GEOS_LIBRARY_PATH = os.environ.get('GEOS_LIBRARY_PATH')
SPATIALITE_LIBRARY_PATH = os.environ.get('SPATIALITE_LIBRARY_PATH')
PROJ_LIB = os.environ.get('PROJ_LIB')

# Добавить поддержку PostGIS с помощью GeoDjango

# Тип поля первичного ключа по умолчанию
# https://docs.djangoproject.com/en/6.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF настройки для продакшн окружения
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if os.environ.get('CSRF_TRUSTED_ORIGINS') else []
