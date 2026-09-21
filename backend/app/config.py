from functools import lru_cache
from typing import List, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LEAKED_DEVELOPMENT_KEY = "campuspulse-super-secret-jwt-key-2026-deterministic-routing"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=True)

    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    PROJECT_NAME: str = "CampusPulse"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./campuspulse.db"

    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    # Work factor for password hashing. Raise as hardware gets faster; lower only in
    # tests, where the cost otherwise dominates the run time.
    BCRYPT_ROUNDS: int = Field(default=12, ge=4, le=16)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 12, ge=5, le=60 * 24 * 7)

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    LOG_JSON: bool = True

    LOGIN_RATE_LIMIT_PER_MINUTE: int = Field(default=10, ge=1)
    REGISTER_RATE_LIMIT_PER_HOUR: int = Field(default=5, ge=1)
    WRITE_RATE_LIMIT_PER_MINUTE: int = Field(default=30, ge=1)

    ALLOWED_ATTACHMENT_SCHEMES: List[str] = ["https"]
    ALLOWED_ATTACHMENT_HOSTS: List[str] = []
    MAX_ATTACHMENT_URL_LENGTH: int = 500

    DEFAULT_PAGE_SIZE: int = Field(default=25, ge=1, le=100)
    MAX_PAGE_SIZE: int = Field(default=100, ge=1, le=500)

    @field_validator("SECRET_KEY")
    @classmethod
    def reject_known_key(cls, value: str) -> str:
        if value.strip() == LEAKED_DEVELOPMENT_KEY:
            raise ValueError(
                "SECRET_KEY is set to the key that was published in this repository's "
                "history. Generate a new one: python -c \"import secrets; "
                "print(secrets.token_urlsafe(48))\""
            )
        return value

    @field_validator("CORS_ORIGINS", "ALLOWED_ATTACHMENT_SCHEMES", "ALLOWED_ATTACHMENT_HOSTS", mode="before")
    @classmethod
    def split_comma_separated(cls, value):
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value

    @model_validator(mode="after")
    def enforce_production_constraints(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if self.BCRYPT_ROUNDS < 12:
                raise ValueError("BCRYPT_ROUNDS must be at least 12 in production")
            if "*" in self.CORS_ORIGINS:
                raise ValueError("CORS_ORIGINS may not contain '*' in production")
            insecure = [o for o in self.CORS_ORIGINS if o.startswith("http://")]
            if insecure:
                raise ValueError(f"CORS_ORIGINS must use https in production: {insecure}")
        return self

    @property
    def docs_enabled(self) -> bool:
        return self.ENVIRONMENT != "production"

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
