from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    APP_TIMEZONE: str = "Europe/Warsaw"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]


settings = Settings()

APP_TZ = ZoneInfo(settings.APP_TIMEZONE)
