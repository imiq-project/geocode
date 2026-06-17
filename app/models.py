"""
Response models for the DYCONET Geocoding Service.
"""

from typing import Optional
from pydantic import BaseModel

# -----------------------------------------
# Response models
# -----------------------------------------
class GeocodeResponse(BaseModel):
    rank: int
    confidence: float
    lat: Optional[float]
    lon: Optional[float]
    display_name: str
    name: Optional[str] = None
    street: Optional[str] = None
    housenumber: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    osm_id: Optional[int] = None
    osm_type: Optional[str] = None
    type: Optional[str] = None
    extent: Optional[list[float]] = None  # [minLon, minLat, maxLon, maxLat]

    model_config = {"json_schema_extra": {
        "example": {
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
            "type": "city",
        }
    }}

#--------------------------
# Request models
#--------------------------
class ReverseResponse(BaseModel):
    query_lat: float
    query_lon: float
    lat: Optional[float]
    lon: Optional[float]
    display_name: str
    name: Optional[str] = None
    street: Optional[str] = None
    housenumber: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    osm_id: Optional[int] = None
    osm_type: Optional[str] = None
    type: Optional[str] = None

    model_config = {"json_schema_extra": {
        "example": {
            "query_lat": 52.1315,
            "query_lon": 11.6399,
            "lat": 52.1315,
            "lon": 11.6399,
            "display_name": "Otto-von-Guericke-Universität, Universitätsplatz 2, 39106 Magdeburg",
            "name": "Otto-von-Guericke-Universität",
            "street": "Universitätsplatz",
            "housenumber": "2",
            "postcode": "39106",
            "city": "Magdeburg",
            "state": "Sachsen-Anhalt",
            "country": "Germany",
            "country_code": "de",
        }
    }}

#-------------------------
# Autocomplete models
#-------------------------
class AutocompleteCandidate(BaseModel):
    display_name: str
    lat: Optional[float]
    lon: Optional[float]
    type: Optional[str] = None
    osm_id: Optional[int] = None

    model_config = {"json_schema_extra": {
        "example": {
            "display_name": "Magdeburger Dom, Domplatz 1, 39104 Magdeburg",
            "lat": 52.1282,
            "lon": 11.6363,
            "type": "place_of_worship",
            "osm_id": 122460,
        }
    }}