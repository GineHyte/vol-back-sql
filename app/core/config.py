import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    SECRET_KEY: str = secrets.token_urlsafe(32)
    PROJECT_NAME: str
    DESCRIPTION: str = ""
    VERSION: str

    SQLITE_DB: str
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"



settings = Settings()
