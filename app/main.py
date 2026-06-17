"""
Geocoding Microservice — Simple Engine
Wraps Nominatim (OSM) with a unified REST API for geocoding, reverse geocoding,
and address autocomplete.

Endpoints:
  POST /geocode        — address string → coordinates + structured address
  POST /reverse        — (lat, lon)     → nearest address
  GET  /autocomplete   — partial string → ranked candidate list
  GET  /health         — liveness check
"""

import time
import hashlib
import logging
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from .config import settings
from .cache import GeoCache
from .models import GeocodeResponse, ReverseResponse, AutocompleteCandidate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geocoding_service")

app = FastAPI(
    title="Simple Engine — Geocoding Service",
    description="Geocoding, reverse geocoding, and autocomplete for Simple Engine.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

cache = GeoCache(maxsize=settings.cache_maxsize, ttl=settings.cache_ttl_seconds)

# Nominatim requires a descriptive User-Agent identifying your application
# See: https://operations.osmfoundation.org/policies/nominatim/
_HEADERS = {
    "User-Agent": f"SimpleEngine-GeocodingService/1.1 ({settings.contact_email})",
    "Accept": "application/json",
}


# ── Request models ─────────────────────────────────────────────────────────────

class GeocodeRequest(BaseModel):
    address: str = Field(..., min_length=2, max_length=500)
    lang: Optional[str] = Field("de", description="Preferred language for result labels")
    limit: Optional[int] = Field(5, ge=1, le=20)

    @field_validator("address")
    @classmethod
    def strip_address(cls, v: str) -> str:
        return v.strip()


class ReverseRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    lang: Optional[str] = Field("de")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _cache_key(*parts) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_nominatim(item: dict) -> dict:
    """Normalise a Nominatim result into our internal flat format."""
    addr = item.get("address", {})
    return {
        "lat": float(item.get("lat", 0)),
        "lon": float(item.get("lon", 0)),
        "display_name": item.get("display_name", ""),
        "name": item.get("name") or addr.get("amenity") or addr.get("building"),
        "street": addr.get("road"),
        "housenumber": addr.get("house_number"),
        "postcode": addr.get("postcode"),
        "city": addr.get("city") or addr.get("town") or addr.get("village"),
        "state": addr.get("state"),
        "country": addr.get("country"),
        "country_code": addr.get("country_code"),
        "osm_id": item.get("osm_id"),
        "osm_type": item.get("osm_type"),
        "type": item.get("type") or item.get("class"),
        "extent": item.get("boundingbox"),
    }


async def _nominatim_search(params: dict) -> list[dict]:
    """Call Nominatim /search and return the results list."""
    base_params = {
        "format": "jsonv2",
        "addressdetails": 1,
        "accept-language": params.pop("lang", "de"),
        **params,
    }
    async with httpx.AsyncClient(timeout=settings.photon_timeout_seconds, headers=_HEADERS) as client:
        try:
            resp = await client.get(settings.nominatim_base_url + "/search", params=base_params)
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Nominatim timed out")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Nominatim returned {e.response.status_code}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Cannot reach Nominatim: {e}")


async def _nominatim_reverse(lat: float, lon: float, lang: str = "de") -> dict:
    """Call Nominatim /reverse and return the single result."""
    params = {
        "format": "jsonv2",
        "addressdetails": 1,
        "lat": lat,
        "lon": lon,
        "accept-language": lang,
    }
    async with httpx.AsyncClient(timeout=settings.photon_timeout_seconds, headers=_HEADERS) as client:
        try:
            resp = await client.get(settings.nominatim_base_url + "/reverse", params=params)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise HTTPException(status_code=404, detail="No address found near these coordinates")
            return data
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Nominatim timed out")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Nominatim returned {e.response.status_code}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Cannot reach Nominatim: {e}")


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    nominatim_ok = False
    try:
        async with httpx.AsyncClient(timeout=3.0, headers=_HEADERS) as client:
            r = await client.get(
                settings.nominatim_base_url + "/search",
                params={"q": "Magdeburg", "format": "jsonv2", "limit": 1},
            )
            nominatim_ok = r.status_code == 200
    except Exception:
        pass
    return {
        "status": "ok" if nominatim_ok else "degraded",
        "nominatim": "reachable" if nominatim_ok else "unreachable",
        "cache_size": cache.size(),
        "timestamp": time.time(),
    }


@app.post("/geocode", response_model=list[GeocodeResponse])
async def geocode(req: GeocodeRequest):
    """Address string → ranked list of candidate locations."""
    key = _cache_key("geocode", req.address.lower(), req.lang, req.limit)
    if cached := cache.get(key):
        return cached

    results_raw = await _nominatim_search({
        "q": req.address,
        "lang": req.lang,
        "limit": req.limit,
        # Bias toward Magdeburg
        "viewbox": "11.5,52.0,11.8,52.2",
        "bounded": 0,  # 0 = prefer viewbox but don't restrict to it
    })

    results = []
    for i, item in enumerate(results_raw):
        parsed = _parse_nominatim(item)
        results.append(GeocodeResponse(
            rank=i + 1,
            confidence=round(max(0.1, 1.0 - i * 0.15), 2),
            **parsed,
        ))

    cache.set(key, results)
    return results


@app.post("/reverse", response_model=ReverseResponse)
async def reverse_geocode(req: ReverseRequest):
    """(lat, lon) → nearest address."""
    key = _cache_key("reverse", round(req.lat, 5), round(req.lon, 5), req.lang)
    if cached := cache.get(key):
        return cached

    item = await _nominatim_reverse(req.lat, req.lon, req.lang or "de")
    parsed = _parse_nominatim(item)
    result = ReverseResponse(query_lat=req.lat, query_lon=req.lon, **parsed)

    cache.set(key, result)
    return result


@app.get("/autocomplete", response_model=list[AutocompleteCandidate])
async def autocomplete(
    q: str = Query(..., min_length=2, max_length=200),
    lang: str = Query("de"),
    limit: int = Query(8, ge=1, le=20),
):
    """Typeahead suggestions for address inputs."""
    key = _cache_key("autocomplete", q.lower().strip(), lang, limit)
    if cached := cache.get(key):
        return cached

    results_raw = await _nominatim_search({
        "q": q,
        "lang": lang,
        "limit": limit,
        "viewbox": "11.5,52.0,11.8,52.2",
        "bounded": 0,
    })

    results = [
        AutocompleteCandidate(
            display_name=_parse_nominatim(item)["display_name"],
            lat=float(item.get("lat", 0)),
            lon=float(item.get("lon", 0)),
            type=item.get("type"),
            osm_id=item.get("osm_id"),
        )
        for item in results_raw
    ]

    cache.set(key, results)
    return results