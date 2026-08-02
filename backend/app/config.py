import logging
from pathlib import Path

from pydantic_settings import BaseSettings

# Repo root is two levels up from this file (backend/app/config.py).
# Load it explicitly so the backend finds .env regardless of CWD.
_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://agentfinance:changeme@localhost:5432/agentfinance"
    opa_url: str = "http://localhost:8181"
    razorpay_mode: str = "test"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    razorpay_debit_identifier: str = ""
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:3000"

    model_config = {"env_file": str(_ROOT_ENV), "extra": "ignore"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

if settings.jwt_secret == "dev-secret-change-in-production":
    logging.getLogger(__name__).warning("JWT_SECRET is the development default — set a real secret in .env")
