# Geocoding Microservice

A lightweight FastAPI-based geocoding service that wraps Nominatim (OpenStreetMap) with a unified REST API for geocoding, reverse geocoding, and address autocomplete.

## Features

- **Geocoding** — Convert address strings to coordinates and structured address data
- **Reverse Geocoding** — Find the nearest address for given coordinates (lat/lon)
- **Autocomplete** — Get ranked candidate suggestions for partial address strings
- **Response Caching** — Built-in TTL-based caching to reduce external API calls
- **CORS Support** — Configurable cross-origin request handling
- **Health Check** — Liveness endpoint for monitoring

## Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (optional)

### Local Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment (create `.env` if needed):
   ```bash
   # Default settings are in app/config.py
   NOMINATIM_BASE_URL=https://nominatim.openstreetmap.org
   CONTACT_EMAIL=your-app@example.com
   CACHE_MAXSIZE=1000
   CACHE_TTL_SECONDS=3600
   ```

3. Run the service:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

4. Open API documentation: http://localhost:8001/docs

### Docker

#### Development (Docker Compose)

```bash
docker-compose up -d
```

#### Self-Hosted

```bash
docker-compose -f docker-compose.selfhosted.yml up -d
```

#### Manual Docker Build

```bash
docker build -t geocoding-service .
docker run -p 8001:8001 geocoding-service
```

## API Endpoints

### POST `/geocode`

Convert an address string to coordinates and structured address data.

**Request:**
```json
{
  "address": "Magdeburg, Germany",
  "lang": "de",
  "limit": 5
}
```

**Response:**
```json
{
  "rank": 1,
  "confidence": 1.0,
  "lat": 52.1205,
  "lon": 11.6276,
  "display_name": "Magdeburg, Sachsen-Anhalt, Germany",
  "city": "Magdeburg",
  "state": "Sachsen-Anhalt",
  "country": "Germany",
  "country_code": "de",
  "osm_id": 62691,
  "osm_type": "R",
  "type": "city"
}
```

**Parameters:**
- `address` (string, required) — Address to geocode (2–500 characters)
- `lang` (string, optional) — Language code for result labels (default: `"de"`)
- `limit` (integer, optional) — Maximum results to return (default: `5`, max: `20`)

---

### POST `/reverse`

Find the nearest address for given coordinates.

**Request:**
```json
{
  "lat": 52.1205,
  "lon": 11.6276,
  "lang": "de"
}
```

**Response:**
```json
{
  "lat": 52.1205,
  "lon": 11.6276,
  "display_name": "Magdeburg, Sachsen-Anhalt, Germany",
  "city": "Magdeburg",
  "country": "Germany",
  "osm_id": 62691,
  "osm_type": "R",
  "type": "city"
}
```

**Parameters:**
- `lat` (float, required) — Latitude (-90 to 90)
- `lon` (float, required) — Longitude (-180 to 180)
- `lang` (string, optional) — Language code (default: `"de"`)

---

### GET `/autocomplete`

Get ranked candidate suggestions for a partial address string.

**Query Parameters:**
- `q` (string, required) — Partial address/query string
- `lang` (string, optional) — Language code (default: `"de"`)
- `limit` (integer, optional) — Maximum results (default: `10`, max: `20`)

**Example:**
```
GET /autocomplete?q=Berlin&lang=de&limit=5
```

**Response:**
```json
[
  {
    "display_name": "Berlin, Germany",
    "lat": 52.5200,
    "lon": 13.4050,
    "type": "city"
  },
  {
    "display_name": "Berlin, Ohio, United States",
    "lat": 40.6082,
    "lon": -81.9034,
    "type": "city"
  }
]
```

---

### GET `/health`

Health check endpoint for monitoring and load balancer probes.

**Response:**
```json
{
  "status": "ok",
  "service": "Geocoding Service",
  "version": "1.1.0"
}
```

## Configuration

Configuration is managed in [app/config.py](app/config.py) using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NOMINATIM_BASE_URL` | `https://nominatim.openstreetmap.org` | Nominatim API base URL |
| `CONTACT_EMAIL` | `app@example.com` | Contact email (used in User-Agent header) |
| `CACHE_MAXSIZE` | `1000` | Maximum number of cached responses |
| `CACHE_TTL_SECONDS` | `3600` | Cache time-to-live in seconds |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |

## Dependencies

- **fastapi** ≥ 0.115.0 — Web framework
- **uvicorn** ≥ 0.30.0 — ASGI server
- **httpx** ≥ 0.27.0 — Async HTTP client
- **pydantic** ≥ 2.7.0 — Data validation
- **pydantic-settings** ≥ 2.3.0 — Configuration management

## Usage Examples

### Python Client

```python
import httpx

async with httpx.AsyncClient() as client:
    # Geocode an address
    response = await client.post(
        "http://localhost:8001/geocode",
        json={"address": "Berlin, Germany", "limit": 5}
    )
    results = response.json()
    print(results)
    
    # Reverse geocode
    response = await client.post(
        "http://localhost:8001/reverse",
        json={"lat": 52.52, "lon": 13.405}
    )
    print(response.json())
```

### cURL

```bash
# Geocode
curl -X POST http://localhost:8001/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "Paris, France", "limit": 3}'

# Reverse geocode
curl -X POST http://localhost:8001/reverse \
  -H "Content-Type: application/json" \
  -d '{"lat": 48.8566, "lon": 2.3522}'

# Autocomplete
curl "http://localhost:8001/autocomplete?q=London&limit=5"

# Health check
curl http://localhost:8001/health
```

## Performance & Caching

The service includes a TTL-based cache to minimize external API requests to Nominatim:

- Responses are cached by request parameters
- Cache entries expire after `CACHE_TTL_SECONDS` (default: 1 hour)
- Maximum `CACHE_MAXSIZE` entries in memory (default: 1000)
- Tune these values based on your workload and memory constraints

## Nominatim Usage Policy

This service wraps Nominatim from OpenStreetMap. Please adhere to their [usage policies](https://operations.osmfoundation.org/policies/nominatim/):

- Identify your application with a meaningful User-Agent (set `CONTACT_EMAIL`)
- Do not overload the API with excessive requests
- Use caching and implement backoff strategies
- Respect rate limits

## Monitoring & Health

- **Health check:** `GET /health` — Always responds with status
- **Liveness probe:** Use `/health` endpoint for Kubernetes or container orchestration
- **Logs:** Application logs are written to stdout with INFO level

## Development

### API Documentation

When running locally, interactive API docs are available at:
- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
