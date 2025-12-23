# GeoPoints Backend Application

Django REST API бэкенд для управления географическими точками на карте: создание точек, обмен сообщениями и пространственный поиск.

⚠️ **Проект использует PostgreSQL + PostGIS. SQLite используется как fallback без spatial index.**

## Архитектурные решения

- PostGIS используется для точных пространственных запросов и индексирования.
- SQLite fallback использует формулу Haversine для простоты и портативности.
- Token аутентификация выбрана для простоты в рамках тестового задания.

## Требования

- Python 3.10+
- Django 4+ или 5+
- Django REST Framework
- PostgreSQL с PostGIS (рекомендуется) или SQLite с SpatiaLite
- GeoDjango

## Установка

1. Клонируйте репозиторий:
  ```bash
  git clone <repository-url>
  cd udrus85_redcollar
  ```

2. Создайте виртуальное окружение:
   ```bash
   python -m venv env
   source env/bin/activate  # На Windows: env\Scripts\activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. База данных (рекомендуется PostGIS):
   - Установите PostgreSQL с расширением PostGIS
   - Создайте базу данных и включите PostGIS:
     ```sql
     CREATE DATABASE geopoints;
     \c geopoints
     CREATE EXTENSION postgis;
     ```
   - Создайте пользователя и выдайте права:
     ```sql
     CREATE USER geopoints_user WITH PASSWORD 'strong_password';
     GRANT CONNECT ON DATABASE geopoints TO geopoints_user;
     GRANT USAGE, CREATE ON SCHEMA public TO geopoints_user;
     ALTER DEFAULT PRIVILEGES IN SCHEMA public
       GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO geopoints_user;
     ALTER DEFAULT PRIVILEGES IN SCHEMA public
       GRANT USAGE, SELECT ON SEQUENCES TO geopoints_user;
     ```

5. **Только для Windows: Установите OSGeo4W для GDAL/GEOS**
   - Скачайте и установите OSGeo4W 64-bit с https://www.osgeo.org/osgeo4w/
   - При установке (Advanced Install) выберите пакеты:
     - `gdal` (GDAL runtime)
     - `geos` (библиотека GEOS)
     - `proj` (библиотека PROJ)
   - Установите переменные окружения (PowerShell):
     ```powershell
     $env:OSGEO4W_ROOT="C:\OSGeo4W"  # или ваш путь установки
     $env:GDAL_LIBRARY_PATH="$env:OSGEO4W_ROOT\bin\gdal312.dll"  # проверьте версию
     $env:GEOS_LIBRARY_PATH="$env:OSGEO4W_ROOT\bin\geos_c.dll"
     $env:PROJ_LIB="$env:OSGEO4W_ROOT\share\proj"
     $env:GDAL_DATA="$env:OSGEO4W_ROOT\share\gdal"
     $env:PATH="$env:OSGEO4W_ROOT\bin;$env:PATH"
     ```
   - Или добавьте их в системные переменные окружения постоянно

6. Установите переменные окружения для подключения к БД:
   ```bash
   # Linux/Mac
   export DB_NAME=geopoints
   export DB_USER=geopoints_user
   export DB_PASSWORD=your_password
   export DB_HOST=localhost
   export DB_PORT=5432
   export USE_POSTGIS=1
   ```
   ```powershell
   # Windows PowerShell
   $env:DB_NAME="geopoints"
   $env:DB_USER="geopoints_user"
   $env:DB_PASSWORD="your_password"
   $env:DB_HOST="localhost"
   $env:DB_PORT="5432"
   $env:USE_POSTGIS="1"
   ```
   - SQLite fallback: если переменные не установлены, приложение использует SQLite (пространственный поиск переключается на Haversine).

7. Выполните миграции:
   ```bash
   python manage.py migrate
   ```

8. Создайте суперпользователя:
   ```bash
   python manage.py createsuperuser
   ```

9. Запустите сервер:
   ```bash
   python manage.py runserver
   ```

## API Эндпоинты

### Аутентификация
Все эндпоинты требуют Token аутентификацию.

- Получение токена: `POST /api/auth/token/` с form data `username`, `password`

### Краткая таблица эндпоинтов

| Метод | Эндпоинт | Описание | Требуется Auth |
|-------|----------|----------|----------------|
| POST | `/api/auth/token/` | Получить токен аутентификации | Нет |
| POST | `/api/points/` | Создать новую точку | Да |
| GET | `/api/points/search/` | Поиск точек в радиусе | Да |
| POST | `/api/points/messages/` | Создать сообщение для точки | Да |
| GET | `/api/points/messages/search/` | Поиск сообщений по локации точки | Да |

### Точки
- **POST /api/points/**: создать точку
  - JSON (любой формат):
    - Lat/Lon: `{ "name": "Название", "description": "Описание", "latitude": 55.75, "longitude": 37.61 }`
    - GeoJSON: `{ "name": "Название", "location": { "type": "Point", "coordinates": [37.61, 55.75] } }`  (lon, lat)

- **GET /api/points/search/?latitude=<lat>&longitude=<lon>&radius=<km>**: поиск точек в радиусе (км)

### Сообщения
- **POST /api/points/messages/**: создать сообщение для точки
  - JSON: `{ "point": <point_id>, "content": "Текст сообщения" }`

- **GET /api/points/messages/search/?latitude=<lat>&longitude=<lon>&radius=<km>**: поиск сообщений по позиции их точек

## Примеры запросов

### Создание точки
```bash
curl -X POST http://localhost:8000/api/points/ \
  -H "Authorization: Token <ваш-токен>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Моя точка", "description": "Опционально", "latitude": 37.7749, "longitude": -122.4194}'
```

### Поиск точек
```bash
curl -X GET "http://localhost:8000/api/points/search/?latitude=37.7749&longitude=-122.4194&radius=10" \
  -H "Authorization: Token <ваш-токен>"
```
При включенном PostGIS поиск использует `distance_lte`. Иначе используется Haversine.

### Создание сообщения
```bash
curl -X POST http://localhost:8000/api/points/messages/ \
  -H "Authorization: Token <ваш-токен>" \
  -H "Content-Type: application/json" \
  -d '{"point": 1, "content": "Привет из этой точки!"}'
```

## Запуск тестов

```bash
# С PostGIS (требуются переменные окружения и готовая БД):
# Убедитесь, что пути GDAL/GEOS/PROJ установлены (см. настройку Windows выше)
# Используйте postgres суперпользователя для тестов (нужны права CREATE EXTENSION)
DB_NAME=geopoints DB_USER=postgres DB_PASSWORD=*** DB_HOST=localhost DB_PORT=5432 USE_POSTGIS=1 \
python manage.py test

# Или с SQLite fallback (PostGIS не требуется):
USE_POSTGIS=0 python manage.py test
```

## Техническое описание

- **Backend**: Django с Django REST Framework
- **База данных**: PostgreSQL с PostGIS для пространственных операций
- **Аутентификация**: Token-based аутентификация
- **Пространственные запросы**: Использует GeoDjango для поиска на основе расстояния
- **Сериализация**: Формат GeoJSON для географических данных

## Структура проекта

- `geopoints/`: Главный проект Django
- `points/`: Приложение с моделями, views, serializers
- `manage.py`: Скрипт управления Django
- `requirements.txt`: Python зависимости

end