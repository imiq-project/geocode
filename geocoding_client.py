"""
GeocodingClient — Simple Engine integration module.

Usage:
    from geocoding_client import GeocodingClient

    client = GeocodingClient()  # reads GEO_SERVICE_URL from env or uses default

    # Forward geocode
    results = await client.geocode("Universitätsplatz 2, Magdeburg")
    lat, lon = results[0].lat, results[0].lon

    # Reverse geocode
    addr = await client.reverse(52.1315, 11.6399)
    print(addr.display_name)

    # Autocomplete (for UI inputs)
    candidates = await client.autocomplete("Magde")
"""

import os
from dataclasses import dataclass
from typing import Optional

import httpx

GEO_SERVICE_URL = os.getenv("GEO_SERVICE_URL", "http://geocoding_service:8001")
DEFAULT_TIMEOUT = float(os.getenv("GEO_TIMEOUT", "5.0"))


@dataclass
class GeoResult:
    rank: int
    confidence: float
    lat: float
    lon: float
    display_name: str
    street: Optional[str] = None
    housenumber: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    osm_id: Optional[int] = None
    type: Optional[str] = None


@dataclass
class ReverseResult:
    query_lat: float
    query_lon: float
    lat: float
    lon: float
    display_name: str
    street: Optional[str] = None
    housenumber: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


@dataclass
class AutocompleteResult:
    display_name: str
    lat: float
    lon: float
    type: Optional[str] = None
    osm_id: Optional[int] = None


# ---------------------------------------
#  Async client for FastAPI / async contexts
# ---------------------------------------

class GeocodingClient:
    """
    Async HTTP client for the DYCONET Geocoding Microservice.
    Suitable for use inside FastAPI / async contexts.
    """

    def __init__(
        self,
        base_url: str = GEO_SERVICE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        lang: str = "de",
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.lang = lang

    async def geocode(
        self,
        address: str,
        limit: int = 5,
        lang: Optional[str] = None,
    ) -> list[GeoResult]:
        """Resolve an address string to a ranked list of candidate locations."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/geocode",
                json={"address": address, "lang": lang or self.lang, "limit": limit},
            )
            resp.raise_for_status()
        return [GeoResult(**r) for r in resp.json()]

    async def geocode_best(self, address: str, lang: Optional[str] = None) -> Optional[GeoResult]:
        """Convenience: return only the top-ranked result, or None if not found."""
        results = await self.geocode(address, limit=1, lang=lang)
        return results[0] if results else None

    async def reverse(
        self,
        lat: float,
        lon: float,
        lang: Optional[str] = None,
    ) -> ReverseResult:
        """Resolve coordinates to the nearest address."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/reverse",
                json={"lat": lat, "lon": lon, "lang": lang or self.lang},
            )
            resp.raise_for_status()
        return ReverseResult(**resp.json())

    async def autocomplete(
        self,
        query: str,
        limit: int = 8,
        lang: Optional[str] = None,
    ) -> list[AutocompleteResult]:
        """Typeahead suggestions for a partial address string."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/autocomplete",
                params={"q": query, "lang": lang or self.lang, "limit": limit},
            )
            resp.raise_for_status()
        return [AutocompleteResult(**r) for r in resp.json()]

    async def health(self) -> dict:
        """Check whether the geocoding service and Photon backend are reachable."""
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{self.base_url}/health")
            return resp.json()


# ---------------------------------------
#  Synchronous convenience wrapper (for non-async callers)
# ---------------------------------------

class SyncGeocodingClient:
    """
    Synchronous wrapper — useful for scripts, Jupyter notebooks,
    or any non-async part of the codebase.
    """

    def __init__(self, base_url: str = GEO_SERVICE_URL, timeout: float = DEFAULT_TIMEOUT, lang: str = "de"):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.lang = lang

    def geocode(self, address: str, limit: int = 5) -> list[GeoResult]:
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(
                f"{self.base_url}/geocode",
                json={"address": address, "lang": self.lang, "limit": limit},
            )
            resp.raise_for_status()
        return [GeoResult(**r) for r in resp.json()]

    def reverse(self, lat: float, lon: float) -> ReverseResult:
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(
                f"{self.base_url}/reverse",
                json={"lat": lat, "lon": lon, "lang": self.lang},
            )
            resp.raise_for_status()
        return ReverseResult(**resp.json())

    def autocomplete(self, query: str, limit: int = 8) -> list[AutocompleteResult]:
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(
                f"{self.base_url}/autocomplete",
                params={"q": query, "lang": self.lang, "limit": limit},
            )
            resp.raise_for_status()
        return [AutocompleteResult(**r) for r in resp.json()]