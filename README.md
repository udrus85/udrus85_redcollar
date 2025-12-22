# GeoPoints Backend Application

A Django REST API backend for managing geographical points on a map, including point creation, messaging, and spatial search functionality.

## Requirements

- Python 3.10+
- Django 4+ or 5+
- Django REST Framework
- PostgreSQL with PostGIS (recommended) or SQLite with SpatiaLite
- GeoDjango

## Installation

1. Clone the repository:
  ```bash
  git clone <repository-url>
  cd udrus85_redcollar
  ```

2. Create a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Database:
  - PostGIS (recommended): install PostGIS on your PostgreSQL server, create DB `geopoints`, enable extension:
    ```sql
    CREATE DATABASE geopoints;
    \c geopoints
    CREATE EXTENSION postgis;
    ```
    Provide env vars: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`. Optionally `USE_POSTGIS=1`.
  - SQLite fallback: if no env vars are set, the app will use SQLite (spatial search falls back to Haversine).

5. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the server:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Authentication
All endpoints require Token authentication.

- Obtain token: `POST /api/auth/token/` with form data `username`, `password`

### Points
- **POST /api/points/**: create a point
  - JSON (either form):
    - Lat/Lon: `{ "name": "Point Name", "description": "Description", "latitude": 55.75, "longitude": 37.61 }`
    - GeoJSON: `{ "name": "Point Name", "location": { "type": "Point", "coordinates": [37.61, 55.75] } }`  (lon, lat)

- **GET /api/points/search/?latitude=<lat>&longitude=<lon>&radius=<km>**: search points within radius (km)

### Messages
- **POST /api/points/messages/**: create a message for a point
  - JSON: `{ "point": <point_id>, "content": "Message content" }`

- **GET /api/points/messages/search/?latitude=<lat>&longitude=<lon>&radius=<km>**: search messages by the position of their point

## Example Requests

### Create Point
```bash
curl -X POST http://localhost:8000/api/points/ \
  -H "Authorization: Token <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Point", "description": "Optional", "latitude": 37.7749, "longitude": -122.4194}'
```

### Search Points
```bash
curl -X GET "http://localhost:8000/api/points/search/?latitude=37.7749&longitude=-122.4194&radius=10" \
  -H "Authorization: Token <your-token>"
```
With PostGIS enabled, search uses `distance_lte`. Otherwise it falls back to Haversine.

### Create Message
```bash
curl -X POST http://localhost:8000/api/points/messages/ \
  -H "Authorization: Token <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"point": 1, "content": "Hello from this point!"}'
```

## Running Tests

```bash
# With SQLite fallback (no PostGIS required):
python manage.py test

# With PostGIS (requires env vars and DB ready):
DB_NAME=geopoints DB_USER=geopoints_user DB_PASSWORD=*** DB_HOST=localhost DB_PORT=5432 USE_POSTGIS=1 \
python manage.py test
```

## Technical Description

- **Backend**: Django with Django REST Framework
- **Database**: PostgreSQL with PostGIS for spatial operations
- **Authentication**: Token-based authentication
- **Spatial Queries**: Uses GeoDjango for distance-based searches
- **Serialization**: GeoJSON format for geographical data

## Project Structure

- `geopoints/`: Main Django project
- `points/`: App containing models, views, serializers
- `manage.py`: Django management script
- `requirements.txt`: Python dependencies

end