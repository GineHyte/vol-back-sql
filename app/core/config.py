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
    ALGORITHM: str = "HS256"
    PROJECT_NAME: str
    DESCRIPTION: str = ""
    VERSION: str

    SQLITE_DB: str
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    LOGFIRE: int = 0
    MINUTES_IN_WEEK: int = 480

    PERCENTAGE_EXERCISES: list = [ 
        (70, 0, 30), # used, unused, learning
        (70, 0, 30),
        (35, 35, 30),
        (35, 35, 30),
        (30, 40, 30),
        (30, 40, 30),
        (25, 45, 30),
        (25, 45, 30),
        (20, 50, 30),
        (20, 50, 30),
        (15, 55, 30),
        (15, 55, 30),
    ]

    LOGGING_CONFIG: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(levelprefix)s %(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "use_colors": True,
            },
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(asctime)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "use_colors": True,
            },
        },
        "handlers": {
            "access": {
                "class": "logging.StreamHandler",
                "formatter": "access",
                "stream": "ext://sys.stdout",
            },
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            "intern": {"handlers": ["default"], "level": "DEBUG", "propagate": False},
            "uvicorn": {"handlers": ["default"], "level": "DEBUG", "propagate": True},
            "uvicorn.access": {
                "handlers": ["access"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {"level": "ERROR", "propagate": False},
            "sqlalchemy.engine": {
                "handlers": ["default"],
                "level": "ERROR",
                "propagate": False,
            },
            "sqlalchemy.engine.Engine": {
                "handlers": ["default"],
                "level": "ERROR",
                "propagate": False,
            },
        },
    }


settings = Settings()
