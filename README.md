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

4. Database (PostGIS recommended):
   - Install PostgreSQL with PostGIS extension
   - Create database and enable PostGIS:
     ```sql
     CREATE DATABASE geopoints;
     \c geopoints
     CREATE EXTENSION postgis;
     ```
   - Create user and grant privileges:
     ```sql
     CREATE USER geopoints_user WITH PASSWORD 'strong_password';
     GRANT CONNECT ON DATABASE geopoints TO geopoints_user;
     GRANT USAGE, CREATE ON SCHEMA public TO geopoints_user;
     ALTER DEFAULT PRIVILEGES IN SCHEMA public
       GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO geopoints_user;
     ALTER DEFAULT PRIVILEGES IN SCHEMA public
       GRANT USAGE, SELECT ON SEQUENCES TO geopoints_user;
     ```

5. **Windows Only: Install OSGeo4W for GDAL/GEOS**
   - Download and install OSGeo4W 64-bit from https://www.osgeo.org/osgeo4w/
   - During installation (Advanced Install), select packages:
     - `gdal` (GDAL runtime)
     - `geos` (GEOS library)
     - `proj` (PROJ library)
   - Set environment variables (PowerShell):
     ```powershell
     $env:OSGEO4W_ROOT="C:\OSGeo4W"  # or your install path
     $env:GDAL_LIBRARY_PATH="$env:OSGEO4W_ROOT\bin\gdal312.dll"  # check actual version
     $env:GEOS_LIBRARY_PATH="$env:OSGEO4W_ROOT\bin\geos_c.dll"
     $env:PROJ_LIB="$env:OSGEO4W_ROOT\share\proj"
     $env:GDAL_DATA="$env:OSGEO4W_ROOT\share\gdal"
     $env:PATH="$env:OSGEO4W_ROOT\bin;$env:PATH"
     ```
   - Or add them to system environment variables permanently

6. Set database connection environment variables:
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
  - SQLite fallback: if no env vars are set, the app will use SQLite (spatial search falls back to Haversine).

5. Run migrations:
   ```bash
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
# With PostGIS (requires env vars and DB ready):
# Ensure GDAL/GEOS/PROJ paths are set (see Windows setup above)
# Use postgres superuser for tests (needs CREATE EXTENSION rights)
DB_NAME=geopoints DB_USER=postgres DB_PASSWORD=*** DB_HOST=localhost DB_PORT=5432 USE_POSTGIS=1 \
python manage.py test

# Or with SQLite fallback (no PostGIS required):
USE_POSTGIS=0 python manage.py test
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