from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "POWER AI API"
    database_url: str = "postgresql+psycopg://power_ai:power_ai_local@localhost:5432/power_ai"
    cors_origins: str = "http://localhost:3000"

    auth_mode: str = "firebase"
    firebase_project_id: str = "demo-power-ai"
    firebase_auth_emulator_host: str | None = None

    ai_provider: str = "mock"
    dev_user_email: str = "student@power.local"
    dev_user_name: str = "POWER Student"

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env", "../../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
