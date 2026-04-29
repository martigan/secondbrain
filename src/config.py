from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    jwt_secret_key: str = Field(default="change-me-too", alias="JWT_SECRET_KEY")
    database_url: str = Field(
        default="postgresql+psycopg://secondbrain:secondbrain@db:5432/secondbrain",
        alias="DATABASE_URL",
    )


def get_settings() -> Settings:
    return Settings()
