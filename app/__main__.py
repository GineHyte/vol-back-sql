import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True, log_config=settings.LOGGING_CONFIG)