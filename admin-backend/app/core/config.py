import os
from pathlib import Path
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent

# Only the backend's own .env is authoritative. Previously the root .env and a
# CWD-relative ".env" were also merged with last-file-wins semantics, which let a
# stray file silently replace JWT_SECRET / ADMIN_PASSWORD / DATABASE_URL.
ENV_PATHS = [str(BACKEND_DIR / ".env")]

DEFAULT_DB_PATH = (ROOT_DIR / "travelogix.db").as_posix()
DEFAULT_DB_URL = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"

# Public placeholder values that must never reach a real deployment.
INSECURE_SECRET_MARKERS = ("insecure_", "change_me", "changeme", "your_", "secret_key_needs_replacement")


class Settings(BaseSettings):
    # Core Application Settings
    PROJECT_NAME: str = "TravelLogix Admin Backend"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 5053

    # Database / Cache
    DATABASE_URL: str = DEFAULT_DB_URL
    SQL_ECHO: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & Auth (no insecure defaults: a missing value must fail loudly)
    JWT_SECRET: str
    CUSTOMER_SESSION_SECRET: str = ""
    ADMIN_SESSION_SECRET: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "travelogix"
    JWT_AUDIENCE: str = "travelogix-api"

    # Rate limiting on authentication endpoints
    AUTH_RATE_LIMIT_ATTEMPTS: int = 5
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Initial Admin Seed
    ADMIN_EMAIL: str = "admin@travelogix.internal"
    ADMIN_PASSWORD: str = "AdminSecurePassword123!"

    # Frontend origins / absolute URLs (never hardcode hosts in code)
    CORS_ORIGINS: str = "http://localhost:3053"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,testserver"
    CUSTOMER_APP_URL: str = "http://localhost:3052"
    ADMIN_APP_URL: str = "http://localhost:3053"
    FRONTEND_BASE_URL: str = "http://localhost:3053"

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:5053/api/v1/auth/customer/google/callback"

    # Demo accounts: development only, never in production
    ENABLE_DEMO_ACCOUNTS: bool = False

    # AI Configuration
    LLM_PROVIDER: str = "gemini"  # "gemini", "groq", "openrouter", "mock"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    OPENROUTER_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_TIMEOUT_SECONDS: float = 15.0
    LLM_MAX_RETRIES: int = 2

    # Travel & Logistics Providers ("mock" means demo data, surfaced as such)
    FLIGHT_PROVIDER: str = "aviationstack"
    FLIGHT_API_KEY: str = ""
    AVIATIONSTACK_API_KEY: str = ""
    TRAIN_PROVIDER: str = "mock"
    TRAIN_API_KEY: str = ""
    BUS_PROVIDER: str = "mock"
    BUS_API_KEY: str = ""
    HOTEL_PROVIDER: str = "mock"
    HOTEL_API_KEY: str = ""
    MAPS_PROVIDER: str = "mock"
    MAPS_API_KEY: str = ""
    WEATHER_PROVIDER: str = "mock"
    WEATHER_API_KEY: str = ""
    COURIER_PROVIDER: str = "mock"
    COURIER_API_KEY: str = ""

    # Regional Defaults
    DEFAULT_COUNTRY: str = "INDIA"
    DEFAULT_CURRENCY: str = "INR"

    model_config = SettingsConfigDict(
        env_file=ENV_PATHS,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # ------------------------------------------------------------------ #
    # Derived values
    # ------------------------------------------------------------------ #
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() not in ("development", "dev", "test", "testing", "local")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_hosts_list(self) -> List[str]:
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

    @property
    def customer_session_secret(self) -> str:
        """Secret used to sign/verify customer tokens (falls back to JWT_SECRET)."""
        return self.CUSTOMER_SESSION_SECRET or self.JWT_SECRET

    @property
    def admin_session_secret(self) -> str:
        """Secret used to sign/verify admin tokens (falls back to JWT_SECRET)."""
        return self.ADMIN_SESSION_SECRET or self.JWT_SECRET

    @property
    def cookie_secure(self) -> bool:
        """Session cookies must be Secure outside local development."""
        return self.is_production

    # ------------------------------------------------------------------ #
    # Fail-fast validation
    # ------------------------------------------------------------------ #
    def insecure_secrets(self) -> List[str]:
        """Names of secret settings still holding a placeholder/dev value."""
        offenders: List[str] = []
        for name in ("JWT_SECRET", "ADMIN_PASSWORD", "CUSTOMER_SESSION_SECRET", "ADMIN_SESSION_SECRET"):
            value = (getattr(self, name, "") or "").strip()
            if not value:
                continue
            lowered = value.lower()
            if any(marker in lowered for marker in INSECURE_SECRET_MARKERS):
                offenders.append(name)
        if (self.ADMIN_PASSWORD or "").strip() == "AdminSecurePassword123!":
            offenders.append("ADMIN_PASSWORD")
        if (self.JWT_SECRET or "").strip() == "super_secret_jwt_key_travelogix_production_ready_32_chars":
            offenders.append("JWT_SECRET")
        return sorted(set(offenders))

    def validate_runtime(self) -> None:
        """
        Refuse to start a non-development deployment that is misconfigured.

        Called from the application lifespan so a bad deploy fails immediately
        instead of silently signing every session with a public key.
        """
        if not self.is_production:
            return

        problems: List[str] = []
        offenders = self.insecure_secrets()
        if offenders:
            problems.append(f"placeholder secret values still in use: {', '.join(offenders)}")
        if self.DEBUG:
            problems.append("DEBUG must be false when ENVIRONMENT is not development")
        if self.SQL_ECHO:
            problems.append("SQL_ECHO must be false outside development (it logs PII with bound parameters)")
        if self.ENABLE_DEMO_ACCOUNTS:
            problems.append("ENABLE_DEMO_ACCOUNTS must be false outside development")
        if "*" in self.cors_origins_list:
            problems.append("CORS_ORIGINS must not contain '*' when credentials are allowed")
        if self.customer_session_secret == self.admin_session_secret:
            problems.append(
                "CUSTOMER_SESSION_SECRET and ADMIN_SESSION_SECRET must differ in production "
                "(otherwise admin and customer tokens are interchangeable)"
            )

        if problems:
            raise RuntimeError(
                "Refusing to start in ENVIRONMENT="
                f"'{self.ENVIRONMENT}': " + "; ".join(problems)
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor (was re-reading .env from disk on every call)."""
    return Settings()
