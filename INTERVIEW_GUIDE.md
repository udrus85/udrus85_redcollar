# Руководство по техническому собеседованию - GeoPoints Backend

## Обзор проекта

**GeoPoints Backend** — это REST API приложение на Django для управления географическими точками на карте с функционалом обмена сообщениями и пространственного поиска.

### Основные возможности
- ✅ Создание и управление географическими точками
- ✅ Прикрепление сообщений к точкам
- ✅ Пространственный поиск в радиусе (км)
- ✅ Token-based аутентификация
- ✅ Поддержка PostGIS и SQLite fallback
- ✅ RESTful API с пагинацией

---

## Технический стек

### Backend
- **Django 4+/5+** — веб-фреймворк
- **Django REST Framework** — REST API
- **GeoDjango** — географические операции
- **PostgreSQL + PostGIS** — основная БД с пространственными индексами
- **SQLite + SpatiaLite** — резервный вариант для разработки

### Ключевые библиотеки
- `djangorestframework-gis` — сериализация геоданных
- `psycopg2-binary` — PostgreSQL адаптер

---

## Архитектура приложения

### Структура проекта
```
udrus85_redcollar/
├── geopoints/          # Django project (настройки, URL)
│   ├── settings.py     # Конфигурация проекта
│   ├── urls.py         # Маршрутизация
│   └── wsgi.py         # WSGI entry point
├── points/             # Django app (модели, views, API)
│   ├── models.py       # Point и Message модели
│   ├── serializers.py  # DRF сериализаторы
│   ├── views.py        # ViewSets для API
│   ├── urls.py         # URL маршруты
│   └── tests.py        # Unit тесты
├── manage.py           # Django CLI
└── requirements.txt    # Python зависимости
```

### Модели данных

#### Point (Географическая точка)
```python
class Point(models.Model):
    user = ForeignKey(User)           # Владелец точки
    name = CharField(max_length=100)  # Название
    description = TextField()         # Описание
    latitude = FloatField()           # Широта
    longitude = FloatField()          # Долгота
    location = PointField()           # PostGIS геометрия (индексируется)
```

**Ключевые особенности:**
- Двойное хранение координат: `latitude/longitude` для портативности + `location` (PostGIS) для производительности
- Автоматическая синхронизация координат в методе `save()`
- География mode (`geography=True`) для точных расчётов на сфере
- SRID 4326 (WGS84) — стандартная система координат GPS

#### Message (Сообщение)
```python
class Message(models.Model):
    user = ForeignKey(User)       # Автор
    point = ForeignKey(Point)     # Привязка к точке
    content = TextField()         # Текст сообщения
    created_at = DateTimeField()  # Время создания
```

**Индексы:**
- `created_at` — для сортировки по времени
- `point.location` — для пространственных запросов

### API эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| `POST` | `/api/auth/token/` | Получение токена аутентификации |
| `POST` | `/api/points/` | Создание новой точки |
| `GET` | `/api/points/` | Список всех точек (пагинация) |
| `GET` | `/api/points/{id}/` | Детали точки |
| `GET` | `/api/points/search/?lat=X&lon=Y&radius=Z` | Поиск точек в радиусе |
| `POST` | `/api/points/messages/` | Создание сообщения |
| `GET` | `/api/points/messages/` | Список сообщений |
| `GET` | `/api/points/messages/search/?lat=X&lon=Y&radius=Z` | Поиск сообщений |

---

## Технические решения и обоснование

### 1. Почему PostGIS + SQLite fallback?

**PostGIS (Production):**
- ✅ Пространственные индексы (GiST) — O(log n) поиск
- ✅ Оптимизированные алгоритмы расстояний
- ✅ Поддержка сложных геометрических операций
- ✅ Масштабируемость для больших данных

**SQLite + Haversine (Development):**
- ✅ Нулевая конфигурация для локальной разработки
- ✅ Портативность (не требует PostgreSQL)
- ⚠️ O(n) поиск — подходит только для малых данных

**Стратегия fallback:**
```python
try:
    # Попытка использовать PostGIS
    qs = Point.objects.filter(location__distance_lte=(center, D(km=radius)))
except (OperationalError, ProgrammingError, GEOSException):
    # Fallback на Haversine
    points = [p for p in Point.objects.all() 
              if _haversine_km(lat, lon, p.latitude, p.longitude) <= radius]
```

### 2. Почему Token Authentication?

**Обоснование:**
- ✅ **Простота** — достаточно для тестового задания
- ✅ **Stateless** — легко масштабируется горизонтально
- ✅ **DRF встроенная поддержка** — из коробки

**Альтернативы в production:**
- JWT (для микросервисов)
- OAuth2 (для сторонних интеграций)
- Session-based (для web-приложений)

### 3. Формат GeoJSON vs Lat/Lon

API поддерживает **оба формата**:

**Формат 1: Latitude/Longitude (простой)**
```json
{
  "name": "Москва",
  "latitude": 55.75,
  "longitude": 37.61
}
```

**Формат 2: GeoJSON (стандартный)**
```json
{
  "name": "Москва",
  "location": {
    "type": "Point",
    "coordinates": [37.61, 55.75]  // [lon, lat] - порядок GeoJSON!
  }
}
```

**Валидация в сериализаторе:**
- Проверка диапазонов: `-90 ≤ lat ≤ 90`, `-180 ≤ lon ≤ 180`
- Проверка конфликта: нельзя передавать оба формата
- Автоматическая конверсия между форматами

### 4. Пагинация

**Настройки:**
```python
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20           # По умолчанию
    page_size_query_param = 'page_size'  # Клиент может изменить
    max_page_size = 100      # Лимит
```

**Зачем?**
- Защита от DoS (ограничение размера ответа)
- Улучшение производительности
- Удобство для клиентов (не нужно загружать всё сразу)

---

## Безопасность

### Реализованные меры

1. **Аутентификация** — все эндпоинты требуют токен
2. **Валидация входных данных:**
   - Диапазоны координат
   - Радиус поиска (0-1000 км)
   - Длина контента сообщений (≤5000 символов)
3. **Django встроенная защита:**
   - CSRF защита
   - SQL injection защита (ORM)
   - XSS защита (автоматический escape)

### Рекомендации для production

⚠️ **Обязательно перед развёртыванием:**
```bash
# 1. Уникальный SECRET_KEY
SECRET_KEY="длинная-случайная-строка-минимум-50-символов"

# 2. Отключить DEBUG
DEBUG=False

# 3. Настроить ALLOWED_HOSTS
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# 4. Настроить CSRF
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# 5. HTTPS only
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## Производительность

### Оптимизации

1. **Пространственные индексы (PostGIS):**
   ```python
   location = PointField(db_index=True, geography=True)
   ```
   - GiST индекс для быстрого поиска по радиусу

2. **Составные индексы:**
   ```python
   indexes = [
       models.Index(fields=['latitude', 'longitude']),
       models.Index(fields=['-created_at']),
   ]
   ```

3. **select_related для сообщений:**
   ```python
   queryset = Message.objects.select_related('point', 'user')
   ```
   - Избегание N+1 запросов

4. **Сортировка по расстоянию:**
   ```python
   qs = qs.annotate(distance=Distance('location', center)).order_by('distance')
   ```

### Масштабирование

**Для больших нагрузок:**
- Read replicas для чтения (PostgreSQL streaming replication)
- Redis для кеширования токенов
- Celery для асинхронных задач (если добавятся тяжёлые операции)
- Nginx + Gunicorn для production

---

## Тестирование

### Покрытие тестами

**Unit тесты (`points/tests.py`):**
- ✅ Создание моделей
- ✅ CRUD операции через API
- ✅ Поиск по радиусу
- ✅ Обработка ошибок PostGIS (fallback)
- ✅ Валидация входных данных

**Запуск тестов:**
```bash
# С PostGIS
USE_POSTGIS=1 python manage.py test

# С SQLite fallback
USE_POSTGIS=0 python manage.py test
```

### Что можно добавить

- [ ] Integration tests (полный workflow)
- [ ] Performance tests (большие датасеты)
- [ ] Security tests (OWASP Top 10)
- [ ] Load testing (с помощью Locust/JMeter)

---

## Возможные улучшения

### Краткосрочные (MVP+)
1. **Пользовательские права:**
   - Только владелец может редактировать/удалять точки
   - Публичные vs приватные точки

2. **Фильтры поиска:**
   - По имени точки
   - По дате создания сообщений
   - По автору

3. **Websockets для real-time:**
   - Уведомления о новых сообщениях
   - Django Channels

### Среднесрочные
1. **Категории точек:**
   - Рестораны, магазины, достопримечательности
   - Иконки на карте

2. **Медиафайлы:**
   - Фото к точкам/сообщениям
   - Django storage + S3/CDN

3. **Рейтинги и отзывы:**
   - Лайки для точек
   - Комментарии к сообщениям

### Долгосрочные
1. **Маршрутизация:**
   - Построение маршрутов между точками
   - Интеграция с OpenStreetMap

2. **Аналитика:**
   - Популярные зоны (heatmap)
   - Статистика использования

3. **Мобильные приложения:**
   - iOS/Android клиенты
   - Push-уведомления

---

## Troubleshooting

### Проблема: "GDAL/GEOS not found" на Windows

**Решение:**
1. Установить OSGeo4W
2. Установить переменные окружения:
```powershell
$env:OSGEO4W_ROOT="C:\OSGeo4W"
$env:GDAL_LIBRARY_PATH="$env:OSGEO4W_ROOT\bin\gdal312.dll"
$env:GEOS_LIBRARY_PATH="$env:OSGEO4W_ROOT\bin\geos_c.dll"
```

### Проблема: PostGIS extension не создается

**Решение:**
```sql
-- Подключиться как суперпользователь
\c geopoints
CREATE EXTENSION postgis;
```

### Проблема: Тесты падают с "permission denied"

**Решение:**
Использовать postgres суперпользователя для тестов:
```bash
DB_USER=postgres DB_PASSWORD=*** python manage.py test
```

---

## Демонстрация на собеседовании

### Подготовка
1. Запустить сервер: `python manage.py runserver`
2. Создать тестового пользователя: `python manage.py createsuperuser`
3. Получить токен через `/api/auth/token/`

### Live Demo сценарий

**Сценарий 1: Создание точек**
```bash
# 1. Получить токен
curl -X POST http://localhost:8000/api/auth/token/ \
  -d "username=testuser&password=testpass"

# 2. Создать точку в Москве
curl -X POST http://localhost:8000/api/points/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Красная площадь", "latitude": 55.7539, "longitude": 37.6208}'

# 3. Создать точку в Санкт-Петербурге
curl -X POST http://localhost:8000/api/points/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Эрмитаж", "latitude": 59.9398, "longitude": 30.3146}'
```

**Сценарий 2: Поиск по радиусу**
```bash
# Найти все точки в радиусе 10 км от центра Москвы
curl -X GET "http://localhost:8000/api/points/search/?latitude=55.7558&longitude=37.6173&radius=10" \
  -H "Authorization: Token YOUR_TOKEN"
```

**Сценарий 3: Сообщения**
```bash
# Создать сообщение к точке
curl -X POST http://localhost:8000/api/points/messages/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"point": 1, "content": "Красивое место!"}'

# Найти сообщения в радиусе
curl -X GET "http://localhost:8000/api/points/messages/search/?latitude=55.7539&longitude=37.6208&radius=5" \
  -H "Authorization: Token YOUR_TOKEN"
```

---

## Вопросы для подготовки

См. файл `INTERVIEW_QA.md` для полного списка вопросов и ответов.

**Основные темы:**
- Архитектура и дизайн решения
- Технические детали реализации
- Безопасность и производительность
- Масштабирование и улучшения
- Альтернативные подходы

---

## Полезные ссылки

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [GeoDjango Tutorial](https://docs.djangoproject.com/en/stable/ref/contrib/gis/tutorial/)
- [PostGIS Documentation](https://postgis.net/docs/)
- [GeoJSON Specification](https://geojson.org/)

---

**Удачи на собеседовании! 🚀**
