# ✅ Чек-лист подготовки к собеседованию

## 📋 За день до собеседования

### 1. Прочитать документацию
- [ ] Прочитать `README.md` — общее описание проекта
- [ ] Прочитать `INTERVIEW_GUIDE.md` — техническое руководство
- [ ] Просмотреть `INTERVIEW_QA.md` — вопросы и ответы (30 вопросов)

### 2. Изучить код
- [ ] `points/models.py` — понять структуру моделей Point и Message
- [ ] `points/views.py` — логика API, пространственный поиск, fallback
- [ ] `points/serializers.py` — валидация, поддержка двух форматов координат
- [ ] `geopoints/settings.py` — конфигурация, PostGIS/SQLite fallback

### 3. Запустить проект локально
```bash
# Установка
git clone https://github.com/udrus85/udrus85_redcollar
cd udrus85_redcollar
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Запуск (SQLite для простоты)
export USE_POSTGIS=0
python manage.py migrate
python manage.py createsuperuser  # username: admin, password: admin
python manage.py runserver
```

### 4. Протестировать API
```bash
# Получить токен
curl -X POST http://localhost:8000/api/auth/token/ \
  -d "username=admin&password=admin"

# Создать точку
curl -X POST http://localhost:8000/api/points/ \
  -H "Authorization: Token ВАШ_ТОКЕН" \
  -H "Content-Type: application/json" \
  -d '{"name": "Тестовая точка", "latitude": 55.75, "longitude": 37.61}'

# Поиск
curl "http://localhost:8000/api/points/search/?latitude=55.75&longitude=37.61&radius=10" \
  -H "Authorization: Token ВАШ_ТОКЕН"
```

---

## 🎯 В день собеседования

### Перед началом (15 минут)
- [ ] Открыть проект в IDE
- [ ] Открыть `INTERVIEW_GUIDE.md` и `INTERVIEW_QA.md` в браузере
- [ ] Запустить сервер: `python manage.py runserver`
- [ ] Убедиться, что можете создать точку через API

### Ключевые темы для обсуждения

#### 1. Обзор проекта (2-3 минуты)
> **"Это REST API для управления географическими точками. Пользователи могут создавать точки с координатами, прикреплять к ним сообщения и искать точки в радиусе. Используется Django + PostGIS для пространственных операций."**

#### 2. Архитектурные решения (5 минут)
Будьте готовы объяснить:
- **Почему двойное хранение координат** (lat/lon + location)
  - Портативность + производительность
- **PostGIS + SQLite fallback**
  - Production: O(log n) с индексами
  - Development: O(n) Haversine
- **Token authentication**
  - Простота для тестового задания
  - Stateless, легко масштабируется

#### 3. Технические детали (5-7 минут)
- **Модели:** Point (с PointField), Message
- **API:** ViewSets, custom action (@action)
- **Поиск:** `distance_lte` + `annotate(distance=Distance(...))`
- **Fallback:** try/except с переключением на Haversine

#### 4. Безопасность (3-5 минут)
- Аутентификация на всех эндпоинтах
- Валидация координат, радиуса, контента
- Production настройки (DEBUG=False, SECRET_KEY, HTTPS)

#### 5. Производительность (3-5 минут)
- Пространственные индексы (GiST)
- Пагинация (max 100 результатов)
- select_related для избежания N+1
- Масштабирование: read replicas, кеширование

---

## 💡 Частые вопросы и краткие ответы

### "Расскажите о проекте"
> REST API для геоточек с поиском по радиусу. Django + PostGIS. Token auth. Fallback на SQLite для dev.

### "Почему PostGIS?"
> Пространственные индексы (O(log n) vs O(n)), оптимизированные алгоритмы расстояний, масштабируемость.

### "Как работает поиск по радиусу?"
> PostGIS: `filter(location__distance_lte=(center, D(km=radius)))` с GiST индексом. Fallback: Python Haversine формула.

### "Что такое geography=True?"
> Расчёты на сфере вместо плоскости. Точные расстояния для GPS координат (WGS84/SRID 4326).

### "Как защищён API?"
> Token auth + валидация входных данных + Django встроенная защита (SQL injection, XSS, CSRF). Production: HTTPS, rate limiting.

### "Как масштабировать?"
> Horizontal: несколько Django воркеров + load balancer. Database: read replicas. Кеширование: Redis. Async: Celery.

### "Какие улучшения можно добавить?"
> Права доступа (только владелец может редактировать), rate limiting, категории точек, медиафайлы, websockets для real-time.

---

## 🎪 Live Demo сценарий

Если попросят показать работу:

```bash
# Терминал 1: Запустить сервер
cd udrus85_redcollar
source venv/bin/activate
python manage.py runserver

# Терминал 2: API запросы
# 1. Получить токен
curl -X POST http://localhost:8000/api/auth/token/ \
  -d "username=admin&password=admin"
# Вывод: {"token": "abcd1234..."}

# 2. Создать точку "Москва"
curl -X POST http://localhost:8000/api/points/ \
  -H "Authorization: Token abcd1234..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Красная площадь",
    "description": "Главная площадь Москвы",
    "latitude": 55.7539,
    "longitude": 37.6208
  }'

# 3. Создать точку "Санкт-Петербург"
curl -X POST http://localhost:8000/api/points/ \
  -H "Authorization: Token abcd1234..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Эрмитаж",
    "latitude": 59.9398,
    "longitude": 30.3146
  }'

# 4. Поиск точек в радиусе 50 км от Москвы
curl "http://localhost:8000/api/points/search/?latitude=55.7558&longitude=37.6173&radius=50" \
  -H "Authorization: Token abcd1234..."
# Должна вернуться только Красная площадь

# 5. Создать сообщение
curl -X POST http://localhost:8000/api/points/messages/ \
  -H "Authorization: Token abcd1234..." \
  -H "Content-Type: application/json" \
  -d '{
    "point": 1,
    "content": "Красивое место для фотографий!"
  }'

# 6. Поиск сообщений в радиусе
curl "http://localhost:8000/api/points/messages/search/?latitude=55.7539&longitude=37.6208&radius=5" \
  -H "Authorization: Token abcd1234..."
```

---

## 📊 Структура кода (для быстрой навигации)

```
udrus85_redcollar/
├── INTERVIEW_GUIDE.md       ← Техническое руководство
├── INTERVIEW_QA.md          ← 30 вопросов и ответов
├── INTERVIEW_CHECKLIST.md   ← Этот файл
├── README.md                ← Документация проекта
│
├── geopoints/               ← Django project
│   ├── settings.py          ← Конфигурация, PostGIS/SQLite
│   └── urls.py              ← /api/auth/token/, /api/ include
│
└── points/                  ← Django app
    ├── models.py            ← Point, Message (43 строки)
    ├── views.py             ← PointViewSet, MessageViewSet (187 строк)
    ├── serializers.py       ← Валидация, lat/lon ↔ GeoJSON (94 строки)
    ├── urls.py              ← Router + custom endpoints
    └── tests.py             ← Unit + integration tests (108 строк)
```

---

## 🔑 Ключевые файлы для показа

### Самые важные:
1. **`points/models.py`** (строки 8-35) — модель Point с автосинхронизацией координат
2. **`points/views.py`** (строки 86-130) — поиск с fallback логикой
3. **`points/serializers.py`** (строки 26-55) — валидация двух форматов

### Интересные моменты:
- **settings.py** (строки 99-119) — PostGIS/SQLite fallback
- **views.py** (строки 58-74) — Haversine формула
- **tests.py** (строки 82-107) — тесты exception handling

---

## 🚀 Уверенность на собеседовании

### Что вы точно знаете:
✅ Проект работает (вы его запустили)  
✅ API функционирует (вы протестировали)  
✅ Архитектура обоснована (прочитали INTERVIEW_GUIDE.md)  
✅ Можете объяснить любое решение (изучили INTERVIEW_QA.md)  

### Фразы для сложных вопросов:
- **"Отличный вопрос. Давайте я покажу в коде..."** (открыть нужный файл)
- **"В текущей версии это не реализовано, но вот как я бы это добавил..."** (показать понимание)
- **"Это trade-off между X и Y. Я выбрал X, потому что..."** (обоснование)

### Если не знаете ответ:
- **"Хороший вопрос, я не сталкивался с этим в данном проекте, но знаю что..."**
- **"Мне нужно уточнить детали, но общий подход такой..."**
- **"Давайте я быстро погуглю и мы обсудим варианты?"** (показывает способность учиться)

---

## 📚 Дополнительные ресурсы

**Если будет время:**
- [ ] Запустить тесты: `python manage.py test`
- [ ] Посмотреть Django admin: http://localhost:8000/admin/
- [ ] Изучить миграции: `points/migrations/`
- [ ] Попробовать GeoJSON формат при создании точки

**Полезные ссылки (можно упомянуть):**
- Django GeoDjango docs
- PostGIS documentation
- GeoJSON specification (RFC 7946)
- Haversine formula

---

## ✨ Финальная проверка

За 5 минут до собеседования:

- [ ] Сервер запущен и работает
- [ ] Можете создать точку через curl/Postman
- [ ] Можете найти точки по радиусу
- [ ] Открыты нужные файлы в IDE
- [ ] Уверены в архитектурных решениях

---

**Вы готовы! Удачи на собеседовании! 🎉**

Помните: вы создали работающий проект с продуманной архитектурой, fallback стратегией, тестами и документацией. Это уже большое достижение!
