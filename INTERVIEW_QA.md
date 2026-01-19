# Вопросы и ответы для собеседования - GeoPoints Backend

## Содержание
1. [Общие вопросы о проекте](#общие-вопросы-о-проекте)
2. [Архитектура и дизайн](#архитектура-и-дизайн)
3. [Технические детали](#технические-детали)
4. [База данных и PostGIS](#база-данных-и-postgis)
5. [API и Django REST Framework](#api-и-django-rest-framework)
6. [Безопасность](#безопасность)
7. [Производительность и масштабирование](#производительность-и-масштабирование)
8. [Тестирование](#тестирование)
9. [DevOps и развёртывание](#devops-и-развёртывание)

---

## Общие вопросы о проекте

### Q1: Расскажите о проекте. Что он делает?

**Ответ:**
GeoPoints Backend — это REST API для управления географическими точками на карте. Основной функционал:
- Пользователи могут создавать точки с координатами (latitude/longitude)
- К каждой точке можно прикреплять сообщения
- Реализован пространственный поиск — найти все точки/сообщения в радиусе X км от заданных координат
- Token-based аутентификация для всех операций

**Типичные use cases:**
- Мобильное приложение для отметок мест на карте (like Foursquare)
- Система обмена сообщениями привязанными к локации
- Поиск ближайших объектов

### Q2: Почему вы выбрали Django?

**Ответ:**
Django был выбран по нескольким причинам:

1. **GeoDjango** — встроенная поддержка географических данных, интеграция с PostGIS/SpatiaLite
2. **Django REST Framework** — мощный и гибкий инструмент для создания REST API
3. **Batteries included** — ORM, миграции, админ-панель, аутентификация из коробки
4. **Безопасность по умолчанию** — защита от CSRF, SQL injection, XSS
5. **Зрелость и документация** — большое сообщество, обширная документация

**Альтернативы:**
- FastAPI (если нужна максимальная производительность)
- Flask + Flask-RESTful (если нужна лёгковесность)
- Node.js + Express (для JS-экосистемы)

### Q3: Сколько времени заняла разработка?

**Ответ:**
Проект был разработан как тестовое задание. Основная реализация заняла примерно:
- Настройка проекта и моделей: 2-3 часа
- API эндпоинты и сериализаторы: 2-3 часа
- Пространственный поиск и fallback логика: 2-3 часа
- Тестирование и отладка: 2-3 часа
- Документация (README): 1-2 часа

**Общее время:** ~10-14 часов

---

## Архитектура и дизайн

### Q4: Почему вы храните координаты дважды (latitude/longitude + location)?

**Ответ:**
Это осознанное архитектурное решение с конкретными целями:

**Причины:**
1. **Портативность:** `latitude/longitude` работают везде (SQLite, любая БД)
2. **Производительность:** `location` (PointField) позволяет использовать пространственные индексы PostGIS
3. **Совместимость API:** Клиенты могут отправлять простые координаты, не зная о GeoJSON

**Синхронизация:**
```python
def save(self, *args, **kwargs):
    if self.latitude and self.longitude:
        self.location = GEOSPoint(self.longitude, self.latitude, srid=4326)
    super().save(*args, **kwargs)
```

**Trade-offs:**
- ✅ Гибкость (работает с/без PostGIS)
- ✅ Удобство для клиентов
- ⚠️ Небольшая избыточность данных (~16 байт vs ~48 байт)
- ⚠️ Нужна синхронизация при bulk операциях

### Q5: Объясните стратегию fallback для PostGIS → Haversine

**Ответ:**
Реализован graceful degradation для случаев, когда PostGIS недоступен:

**Стратегия:**
```python
try:
    # Попытка использовать PostGIS (быстро, O(log n) с индексом)
    center = GEOSPoint(lon, lat, srid=4326)
    qs = Point.objects.filter(location__distance_lte=(center, D(km=radius)))
    qs = qs.annotate(distance=Distance('location', center)).order_by('distance')
except (OperationalError, ProgrammingError, GEOSException):
    # Fallback на Python Haversine (медленно, O(n))
    points = [p for p in Point.objects.all() 
              if _haversine_km(lat, lon, p.latitude, p.longitude) <= radius]
```

**Формула Haversine:**
Вычисляет расстояние по сфере между двумя точками:
```python
def _haversine_km(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * earth_radius_km * atan2(sqrt(a), sqrt(1-a))
```

**Когда срабатывает fallback:**
- SQLite без SpatiaLite
- PostGIS не установлен/не настроен
- Ошибки конфигурации GEOS/GDAL

### Q6: Почему вы используете PointField с geography=True?

**Ответ:**
`geography=True` — это критически важная настройка для точности расстояний:

**Geometry vs Geography:**

| Режим | Система | Точность | Производительность |
|-------|---------|----------|-------------------|
| `geography=False` | Плоская проекция | Искажения на больших расстояниях | Быстрее |
| `geography=True` | Сферическая Земля | Высокая точность | Немного медленнее |

**Пример искажений:**
- Расстояние Москва-СПб: ~700 км (реальное)
- С geometry: ~650-750 км (зависит от проекции)
- С geography: ~705 км (точное сферическое расстояние)

**Вывод:** Для глобальных координат (GPS) всегда используем `geography=True`.

### Q7: Как вы обрабатываете разные форматы координат (lat/lon vs GeoJSON)?

**Ответ:**
Сериализатор поддерживает оба формата с автоматической конверсией:

**Валидация в PointSerializer:**
```python
def validate(self, data):
    location = data.get('location')
    lat, lon = data.get('latitude'), data.get('longitude')
    
    # 1. Проверка конфликта
    if location and (lat or lon):
        raise ValidationError("Нельзя передавать оба формата")
    
    # 2. Проверка что хотя бы один формат есть
    if not location and (lat is None or lon is None):
        raise ValidationError("Нужен либо location, либо lat/lon")
    
    # 3. Валидация SRID
    if location and location.srid != 4326:
        location.transform(4326)
    
    return data
```

**Пример запросов:**
```json
// Формат 1: Простые координаты
{"name": "Точка", "latitude": 55.75, "longitude": 37.61}

// Формат 2: GeoJSON
{"name": "Точка", "location": {"type": "Point", "coordinates": [37.61, 55.75]}}
```

⚠️ **Важно:** В GeoJSON координаты идут в порядке `[longitude, latitude]`!

---

## Технические детали

### Q8: Расскажите о структуре моделей

**Ответ:**

**Point модель:**
```python
class Point(models.Model):
    user = ForeignKey(User, on_delete=CASCADE)     # Владелец
    name = CharField(max_length=100)               # Название
    description = TextField(blank=True)            # Описание
    latitude = FloatField()                        # Широта [-90, 90]
    longitude = FloatField()                       # Долгота [-180, 180]
    location = PointField(geography=True, srid=4326, db_index=True)
```

**Ключевые решения:**
- `on_delete=CASCADE` — удаление точки удаляет все её сообщения
- `db_index=True` на location — GiST индекс для быстрого поиска
- `srid=4326` — WGS84, стандартная система GPS

**Message модель:**
```python
class Message(models.Model):
    user = ForeignKey(User, on_delete=CASCADE)
    point = ForeignKey(Point, on_delete=CASCADE, related_name='messages')
    content = TextField(max_length=5000)
    created_at = DateTimeField(auto_now_add=True)
```

**Индексы:**
- `created_at` с префиксом `-` для сортировки по убыванию
- `related_name='messages'` — для обратных запросов: `point.messages.all()`

### Q9: Как работает метод save() в Point?

**Ответ:**
Переопределён для автоматической синхронизации координат:

```python
def save(self, *args, **kwargs):
    if self.latitude is not None and self.longitude is not None:
        self.location = GEOSPoint(self.longitude, self.latitude, srid=4326)
    super().save(*args, **kwargs)
```

**Что происходит:**
1. Проверяем что координаты заданы
2. Создаём GEOSPoint с правильным SRID
3. ⚠️ Порядок: `GEOSPoint(lon, lat)` — не перепутать!
4. Вызываем родительский save() для записи в БД

**Ограничения:**
- Не работает с `bulk_create()` — обходит save()
- Не работает с `QuerySet.update()` — тоже обходит save()
- Для bulk операций нужно вручную заполнять location

### Q10: Объясните логику пагинации

**Ответ:**
Используется стандартная пагинация DRF с кастомными настройками:

```python
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20                     # По умолчанию 20 объектов
    page_size_query_param = 'page_size' # Клиент может изменить
    max_page_size = 100                 # Но не больше 100
```

**Как использовать:**
```bash
# Первая страница (по умолчанию 20 результатов)
GET /api/points/?page=1

# Вторая страница с 50 результатами
GET /api/points/?page=2&page_size=50

# Ошибка: page_size > 100 будет ограничен до 100
GET /api/points/?page_size=500  # Вернёт 100
```

**Ответ API:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/points/?page=2",
  "previous": null,
  "results": [/* 20 объектов */]
}
```

**Зачем:**
- Защита от DoS (нельзя запросить миллион объектов)
- Производительность (не загружаем всё в память)
- UX (progressive loading)

---

## База данных и PostGIS

### Q11: Что такое SRID и почему 4326?

**Ответ:**
**SRID (Spatial Reference System Identifier)** — идентификатор системы координат.

**SRID 4326 = WGS84:**
- Стандартная система GPS
- Используется Google Maps, OpenStreetMap, GPS устройствами
- Координаты: latitude (широта) и longitude (долгота) в градусах
- Диапазоны: lat ∈ [-90°, 90°], lon ∈ [-180°, 180°]

**Другие популярные SRID:**
- **3857 (Web Mercator)** — используется для отображения карт в браузере
- **4269 (NAD83)** — Северная Америка
- **32636 (UTM Zone 36N)** — локальная проекция для России

**Почему важно:**
- Расстояния правильно считаются только в одной системе
- PostGIS автоматически трансформирует при необходимости
- Смешивание SRID без трансформации даёт неверные результаты

### Q12: Как работают пространственные индексы в PostGIS?

**Ответ:**
PostGIS использует **GiST (Generalized Search Tree)** индекс:

**Принцип работы:**
1. Пространство разбивается на bounding boxes (прямоугольники)
2. Индекс строит дерево этих box'ов
3. При поиске быстро исключаем удалённые области
4. Детальная проверка только для кандидатов

**Создание:**
```python
# В Django
location = PointField(db_index=True, geography=True)

# Генерирует SQL
CREATE INDEX ON points USING GIST (location);
```

**Производительность:**
- Без индекса: O(n) — проверка всех точек
- С индексом: O(log n) — быстрый поиск
- На 1 млн точек: ~5 мс vs ~1000 мс

**Размер:** ~50-100 байт на точку (зависит от плотности данных)

### Q13: Чем отличается distance_lte от distance_lt?

**Ответ:**

| Фильтр | SQL эквивалент | Значение |
|--------|----------------|----------|
| `distance_lte` | `<=` | Less Than or Equal (включительно) |
| `distance_lt` | `<` | Less Than (строго меньше) |
| `distance_gte` | `>=` | Greater Than or Equal |
| `distance_gt` | `>` | Greater Than |

**Пример:**
```python
# Все точки в радиусе 5 км (включая ровно 5 км)
Point.objects.filter(location__distance_lte=(center, D(km=5)))

# Все точки строго ближе 5 км (5.0 км не войдёт)
Point.objects.filter(location__distance_lt=(center, D(km=5)))
```

**Практика:** Обычно используется `distance_lte` (inclusive), т.к. пользователи ожидают "в радиусе 5 км" = "до 5 км включительно".

### Q14: Что будет, если не установить PostGIS?

**Ответ:**
Приложение автоматически переключится на SQLite + Haversine fallback:

**Поведение:**
1. Django попытается выполнить PostGIS запрос
2. Поймает `OperationalError` или `ProgrammingError`
3. Fallback на Python-реализацию Haversine
4. Логирование: `"PostGIS query failed, falling back to Haversine"`

**Ограничения fallback:**
- ⚠️ O(n) сложность — медленно на больших данных
- ⚠️ Нет сортировки по расстоянию
- ⚠️ Загружает все точки в память
- ✅ Работает везде (даже на чистом SQLite)

**Когда допустимо:**
- Локальная разработка
- Малые датасеты (<1000 точек)
- Прототипирование

**Production:** Всегда используйте PostGIS!

---

## API и Django REST Framework

### Q15: Почему вы используете ViewSets вместо APIView?

**Ответ:**
**ViewSet** предоставляет больше возможностей из коробки:

**Преимущества ViewSet:**
```python
class PointViewSet(viewsets.ModelViewSet):
    queryset = Point.objects.all()
    serializer_class = PointSerializer
    # Автоматически получаем:
    # - list() — GET /points/
    # - create() — POST /points/
    # - retrieve() — GET /points/{id}/
    # - update() — PUT /points/{id}/
    # - partial_update() — PATCH /points/{id}/
    # - destroy() — DELETE /points/{id}/
```

**Custom actions:**
```python
@action(detail=False, methods=['get'])
def search(self, request):
    # Custom эндпоинт: GET /points/search/
    ...
```

**Альтернатива — APIView:**
Пришлось бы писать каждый метод вручную:
```python
class PointListCreate(APIView):
    def get(self, request): ...
    def post(self, request): ...

class PointDetail(APIView):
    def get(self, request, pk): ...
    def put(self, request, pk): ...
    def delete(self, request, pk): ...
```

**Вывод:** ViewSet = меньше boilerplate кода, больше стандартизации.

### Q16: Как работает аутентификация по токену?

**Ответ:**

**Flow:**
1. **Регистрация/Создание пользователя:**
   ```bash
   python manage.py createsuperuser
   ```

2. **Получение токена:**
   ```bash
   POST /api/auth/token/
   Body: username=admin&password=secret
   
   Response: {"token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"}
   ```

3. **Использование токена:**
   ```bash
   GET /api/points/
   Header: Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
   ```

**Настройка DRF:**
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

**Хранение токена:**
- В БД таблица `authtoken_token`
- 1 токен на пользователя (unless regenerated)
- Хеширование не требуется (токен сам по себе случайный)

**Безопасность:**
- Передача только через HTTPS в production
- Хранение в secure storage на клиенте (не localStorage!)
- Ротация токенов при компрометации

### Q17: Почему perform_create вместо переопределения create?

**Ответ:**
`perform_create` — это hook для бизнес-логики без изменения ответа:

**Правильно (текущий код):**
```python
def perform_create(self, serializer):
    serializer.save(user=self.request.user)
```

**Неправильно (избыточно):**
```python
def create(self, request):
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user)  # Дублируем логику DRF
    return Response(serializer.data, status=status.HTTP_201_CREATED)
```

**Разница:**

| Метод | Назначение | Когда переопределять |
|-------|-----------|---------------------|
| `perform_create()` | Логика сохранения | Добавить пользователя, логирование |
| `create()` | Весь HTTP flow | Изменить status code, headers, ответ |

**Преимущества perform_create:**
- Короче код
- Не дублируем валидацию
- Работает с mixins
- Легче тестировать

### Q18: Как вы валидируете входные данные?

**Ответ:**
Многоуровневая валидация:

**Уровень 1: Field-level validation**
```python
def validate_latitude(self, value):
    if value is not None and not (-90 <= value <= 90):
        raise ValidationError("Широта должна быть в диапазоне от -90 до 90.")
    return value
```

**Уровень 2: Object-level validation**
```python
def validate(self, data):
    location = data.get('location')
    lat, lon = data.get('latitude'), data.get('longitude')
    
    if location and (lat or lon):
        raise ValidationError("Нельзя передавать оба формата")
    
    return data
```

**Уровень 3: View-level validation**
```python
def _parse_geo_params(request):
    lat, lon, radius = ...
    if radius <= 0 or radius > 1000:
        return None, None, None, Response({'error': '...'}, status=400)
```

**Уровень 4: Model constraints**
```python
class Meta:
    constraints = [
        models.CheckConstraint(
            check=Q(latitude__gte=-90) & Q(latitude__lte=90),
            name='valid_latitude'
        )
    ]
```

**Когда какой уровень:**
- Field-level: простые правила для одного поля
- Object-level: правила для нескольких полей
- View-level: бизнес-логика, query параметры
- Model constraints: последний рубеж защиты

---

## Безопасность

### Q19: Какие меры безопасности реализованы?

**Ответ:**

**1. Аутентификация:**
- Token-based — все эндпоинты защищены
- Только авторизованные пользователи могут создавать/читать данные

**2. Валидация входных данных:**
```python
# Координаты
-90 <= latitude <= 90
-180 <= longitude <= 180

# Радиус поиска
0 < radius <= 1000 км

# Контент сообщений
1 <= len(content) <= 5000 символов
```

**3. Django встроенная защита:**
- **SQL Injection** — Django ORM экранирует запросы
- **XSS** — Django templates автоматически экранируют вывод
- **CSRF** — токены для форм (для API не критично, т.к. token auth)
- **Clickjacking** — X-Frame-Options header

**4. Настройки для production:**
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

### Q20: Как защититься от злоупотреблений API?

**Ответ:**
Текущая защита + рекомендации:

**Реализовано:**
1. **Пагинация:** max 100 объектов на запрос
2. **Валидация радиуса:** max 1000 км для поиска
3. **Лимит контента:** max 5000 символов в сообщении

**Нужно добавить:**
1. **Rate limiting (DRF Throttling):**
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',    # Неавторизованные
        'user': '1000/hour'    # Авторизованные
    }
}
```

2. **Права доступа:**
```python
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user
```

3. **Celery для тяжёлых операций:**
- Асинхронная обработка больших радиусов
- Защита от блокировки воркеров

4. **Monitoring:**
- Логирование подозрительной активности
- Alerts на аномальные запросы

### Q21: Как вы храните SECRET_KEY?

**Ответ:**
**Текущая реализация (development):**
```python
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default...')
```

**Production best practices:**

1. **Переменные окружения:**
```bash
export SECRET_KEY="длинная-случайная-строка-минимум-50-символов"
```

2. **Secret management системы:**
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault
   - Kubernetes Secrets

3. **Генерация сильного ключа:**
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

4. **Никогда не коммитить в Git:**
```gitignore
# .gitignore
.env
*.env.local
secrets/
```

**Что будет при утечке:**
- Подделка CSRF токенов
- Подделка signed cookies
- Компрометация сессий
- **Решение:** Немедленная ротация + аудит сессий

---

## Производительность и масштабирование

### Q22: Как приложение будет работать с миллионом точек?

**Ответ:**

**С PostGIS — отлично:**
- GiST индекс: O(log n) поиск
- Spatial index сужает поиск до небольшой области
- Пагинация предотвращает большие выборки
- **Ожидаемое время:** 5-20 мс на запрос

**Тесты производительности (с индексом):**
```
100K точек:  ~5 мс
1M точек:    ~10 мс
10M точек:   ~20 мс
```

**Без PostGIS (SQLite fallback) — плохо:**
- O(n) сканирование всех точек
- Вся таблица загружается в память
- **Ожидаемое время:** 100-1000+ мс на 1M точек

### Q23: Как масштабировать приложение?

**Ответ:**

**Вертикальное масштабирование:**
- Больше RAM для PostgreSQL (shared_buffers)
- Faster SSD для индексов
- Больше CPU cores для параллельных запросов

**Горизонтальное масштабирование:**

**1. Application layer (Django):**
```
           Load Balancer (Nginx)
                  |
    +-------------+-------------+
    |             |             |
Django App 1  Django App 2  Django App 3
```
- Stateless design (Token auth) позволяет легко добавлять воркеры
- Gunicorn/uWSGI для production

**2. Database layer (PostgreSQL):**
```
       Master (Write)
          |
    ------+------
    |           |
Replica 1   Replica 2  (Read-only)
```
- Read replicas для поисковых запросов
- Master для создания точек/сообщений
- Django database routing

**3. Кеширование (Redis):**
```python
# Кеш популярных областей
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
    }
}

# Кеширование токенов
@cache_page(60 * 15)  # 15 минут
def search(self, request):
    ...
```

**4. CDN для статики:**
- Staticfiles на S3/CloudFront
- Offload Django от serving static

**5. Асинхронные задачи (Celery):**
```python
# Для очень больших радиусов
@celery_app.task
def search_large_radius(lat, lon, radius):
    ...
```

### Q24: Какие индексы вы используете?

**Ответ:**

**Созданные индексы:**
```python
# 1. Пространственный индекс на location
location = PointField(db_index=True, geography=True)
# SQL: CREATE INDEX ON points USING GIST (location);

# 2. Составной индекс на координаты
class Meta:
    indexes = [
        models.Index(fields=['latitude', 'longitude']),
    ]
# SQL: CREATE INDEX ON points (latitude, longitude);

# 3. Индекс на created_at с DESC порядком
class Meta:
    indexes = [
        models.Index(fields=['-created_at']),
    ]
# SQL: CREATE INDEX ON messages (created_at DESC);
```

**Автоматические индексы:**
- Primary keys (id)
- Foreign keys (user_id, point_id)

**Анализ использования:**
```sql
-- Проверка использования индексов
EXPLAIN ANALYZE
SELECT * FROM points 
WHERE ST_DWithin(location, ST_MakePoint(37.61, 55.75)::geography, 5000);
```

**Trade-offs:**
- ✅ Ускоряют SELECT
- ⚠️ Замедляют INSERT/UPDATE/DELETE (~10-20%)
- ⚠️ Занимают место на диске (~10-30% от таблицы)

**Вывод:** Индексы критичны для read-heavy приложений (карты, поиск).

### Q25: Как оптимизировать N+1 запросы?

**Ответ:**
**Проблема:** При загрузке сообщений Django делает N запросов для связанных точек.

**Плохо (N+1 запросы):**
```python
messages = Message.objects.all()  # 1 запрос
for msg in messages:
    print(msg.point.name)  # N запросов (по одному на каждое сообщение)
```

**Хорошо (1 запрос с JOIN):**
```python
# В коде
messages = Message.objects.select_related('point', 'user')  # 1 запрос с JOIN

# В ViewSet
queryset = Message.objects.select_related('point', 'user')
```

**SQL разница:**
```sql
-- Без select_related (N+1 запросы)
SELECT * FROM messages;
SELECT * FROM points WHERE id=1;
SELECT * FROM points WHERE id=2;
...

-- С select_related (1 запрос)
SELECT * FROM messages
LEFT JOIN points ON messages.point_id = points.id
LEFT JOIN users ON messages.user_id = users.id;
```

**Другие методы:**
- `prefetch_related()` — для many-to-many и reverse FK
- `only()` / `defer()` — загрузка только нужных полей
- `annotate()` — агрегация в БД вместо Python

---

## Тестирование

### Q26: Какие типы тестов вы написали?

**Ответ:**

**1. Model Tests:**
```python
def test_point_creation(self):
    point = Point.objects.create(user=self.user, name='Test', ...)
    self.assertEqual(point.name, 'Test')
```

**2. API Tests (Integration):**
```python
def test_create_point(self):
    response = self.client.post('/api/points/', {...})
    self.assertEqual(response.status_code, 201)
```

**3. Search Tests:**
```python
def test_search_points(self):
    Point.objects.create(...)  # В радиусе
    response = self.client.get('/api/points/search/?lat=0&lon=0&radius=5')
    self.assertEqual(len(response.data), 1)
```

**4. Exception Handling Tests:**
```python
@patch('points.views.Point.objects.filter')
def test_fallback_to_haversine(self, mock_filter):
    mock_filter.side_effect = OperationalError()
    response = self.client.get('/api/points/search/?...')
    self.assertEqual(response.status_code, 200)  # Fallback сработал
```

**Покрытие:**
- Models: ✅ Создание, связи
- API: ✅ CRUD операции
- Search: ✅ Пространственный поиск
- Auth: ✅ Token authentication
- Fallback: ✅ PostGIS → Haversine

### Q27: Как запустить тесты?

**Ответ:**

**С PostGIS:**
```bash
# Экспортировать переменные окружения
export USE_POSTGIS=1
export DB_NAME=geopoints_test
export DB_USER=postgres  # Нужны права на CREATE EXTENSION
export DB_PASSWORD=***
export DB_HOST=localhost
export DB_PORT=5432

# Запустить тесты
python manage.py test

# Запустить конкретное приложение
python manage.py test points

# Запустить конкретный тест
python manage.py test points.tests.PointAPITest.test_create_point
```

**С SQLite (без PostGIS):**
```bash
export USE_POSTGIS=0
python manage.py test
```

**С coverage:**
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Генерирует htmlcov/index.html
```

**CI/CD (GitHub Actions пример):**
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:14-3.2
        env:
          POSTGRES_PASSWORD: postgres
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: python manage.py test
```

### Q28: Что ещё нужно протестировать?

**Ответ:**

**Unit тесты (добавить):**
- [ ] Валидация сериализаторов (все edge cases)
- [ ] Haversine формула (точность)
- [ ] Синхронизация координат в save()
- [ ] SRID трансформации

**Integration тесты:**
- [ ] Полный workflow: создать пользователя → токен → точка → сообщение → поиск
- [ ] Pagination (edge cases: page=0, page=999999)
- [ ] Сортировка по расстоянию

**Performance тесты:**
- [ ] Load testing (1000+ одновременных запросов)
- [ ] Search на большом датасете (100K+ точек)
- [ ] Индекс эффективность (EXPLAIN ANALYZE)

**Security тесты:**
- [ ] Попытка доступа без токена
- [ ] Попытка изменить чужую точку
- [ ] SQL injection attempts
- [ ] Большие payload (DoS защита)

**E2E тесты:**
- [ ] Selenium для фронтенда (если есть)
- [ ] Mobile app тестирование

---

## DevOps и развёртывание

### Q29: Как развернуть приложение в production?

**Ответ:**

**Шаг 1: Подготовка сервера (Ubuntu)**
```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить зависимости
sudo apt install -y python3-pip python3-venv postgresql postgis nginx

# Установить PostgreSQL + PostGIS
sudo apt install -y postgresql-14 postgresql-14-postgis-3
```

**Шаг 2: Настройка PostgreSQL**
```sql
CREATE DATABASE geopoints;
\c geopoints
CREATE EXTENSION postgis;
CREATE USER geopoints_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE geopoints TO geopoints_user;
```

**Шаг 3: Настройка приложения**
```bash
# Клонировать репозиторий
git clone https://github.com/udrus85/udrus85_redcollar
cd udrus85_redcollar

# Создать venv
python3 -m venv venv
source venv/bin/activate

# Установить зависимости + production пакеты
pip install -r requirements.txt
pip install gunicorn

# Установить переменные окружения
export SECRET_KEY="..."  # Сгенерировать новый!
export DEBUG="False"
export ALLOWED_HOSTS="yourdomain.com"
export DB_NAME="geopoints"
export DB_USER="geopoints_user"
export DB_PASSWORD="..."
export USE_POSTGIS="1"

# Миграции
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --no-input
```

**Шаг 4: Gunicorn service**
```ini
# /etc/systemd/system/geopoints.service
[Unit]
Description=GeoPoints Django App
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/udrus85_redcollar
Environment="PATH=/var/www/udrus85_redcollar/venv/bin"
EnvironmentFile=/etc/geopoints.env
ExecStart=/var/www/udrus85_redcollar/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/geopoints.sock \
    geopoints.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Шаг 5: Nginx**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /var/www/udrus85_redcollar/staticfiles/;
    }

    location / {
        proxy_pass http://unix:/run/geopoints.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Шаг 6: SSL (Let's Encrypt)**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

**Шаг 7: Запуск**
```bash
sudo systemctl start geopoints
sudo systemctl enable geopoints
sudo systemctl restart nginx
```

### Q30: Как мониторить приложение в production?

**Ответ:**

**1. Логирование:**
```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/geopoints/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
        },
        'points': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    },
}
```

**2. Мониторинг производительности:**
- **Sentry** — ошибки и трейсы
- **New Relic / DataDog** — APM (Application Performance Monitoring)
- **Prometheus + Grafana** — метрики

**3. Database мониторинг:**
```sql
-- Медленные запросы
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Размер индексов
SELECT schemaname, tablename, indexname, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

**4. Health checks:**
```python
# views.py
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    try:
        Point.objects.count()  # Проверка БД
        return Response({'status': 'healthy'})
    except Exception as e:
        return Response({'status': 'unhealthy', 'error': str(e)}, status=500)
```

**5. Uptime monitoring:**
- UptimeRobot
- Pingdom
- AWS CloudWatch

---

## Заключение

### Ключевые моменты для собеседования:

✅ **Понимание бизнес-задачи** — управление геоточками, поиск по радиусу
✅ **Обоснование технологий** — Django + PostGIS для пространственных операций
✅ **Архитектурные решения** — двойное хранение координат, fallback механизм
✅ **Безопасность** — валидация, аутентификация, production настройки
✅ **Производительность** — индексы, пагинация, select_related
✅ **Тестируемость** — unit, integration, fallback тесты
✅ **Масштабируемость** — read replicas, кеширование, горизонтальное масштабирование

### Дополнительные материалы:
- `INTERVIEW_GUIDE.md` — техническое руководство
- `README.md` — документация проекта
- `requirements.txt` — список зависимостей

**Удачи на собеседовании! 🚀**
