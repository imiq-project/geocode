from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Nominatim backend
    # DEV:  https://nominatim.openstreetmap.org  (public, free, 1 req/sec limit)
    # PROD: http://nominatim:8080                (self-hosted via Docker)
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"

    # Nominatim usage policy requires a contact email in the User-Agent header
    # Set this to your real email: GEO_CONTACT_EMAIL=your@email.com
    contact_email: str = "your@email.com"

    # Location bias — Magdeburg city centre
    bias_lat: float = 52.1205
    bias_lon: float = 11.6276

    # Request timeout
    photon_timeout_seconds: float = 8.0

    # Cache
    cache_maxsize: int = 2000
    cache_ttl_seconds: int = 3600

    # CORS
    cors_origins: list[str] = ["*"]

    model_config = {"env_prefix": "GEO_", "env_file": ".env"}


settings = Settings()