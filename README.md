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
   cd geopoints
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

4. Set up the database:
   - For PostgreSQL with PostGIS:
     - Install PostgreSQL and PostGIS
     - Create a database named `geopoints_db`
     - Update `settings.py` with your database credentials
   - For SQLite with SpatiaLite:
     - Install SpatiaLite
     - The database will be created automatically

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
All endpoints require authentication. Use Token authentication.

- Obtain token: POST `/api-auth/token/` with username and password

### Points
- **POST /api/points/**: Create a new point
  - Body: `{"name": "Point Name", "description": "Description", "location": {"type": "Point", "coordinates": [longitude, latitude]}}`

- **GET /api/points/search/?lat=<lat>&lon=<lon>&radius=<km>**: Search points within radius

### Messages
- **POST /api/messages/**: Create a message for a point
  - Body: `{"point": <point_id>, "content": "Message content"}`

- **GET /api/messages/search/?lat=<lat>&lon=<lon>&radius=<km>**: Search messages within radius

## Example Requests

### Create Point
```bash
curl -X POST http://localhost:8000/api/points/ \
  -H "Authorization: Token <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Point", "location": {"type": "Point", "coordinates": [37.7749, -122.4194]}}'
```

### Search Points
```bash
curl -X GET "http://localhost:8000/api/points/search/?lat=37.7749&lon=-122.4194&radius=10" \
  -H "Authorization: Token <your-token>"
```

### Create Message
```bash
curl -X POST http://localhost:8000/api/messages/ \
  -H "Authorization: Token <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"point": 1, "content": "Hello from this point!"}'
```

## Running Tests

```bash
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