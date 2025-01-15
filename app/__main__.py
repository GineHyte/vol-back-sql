import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True, host="0.0.0.0", log_config=settings.LOGGING_CONFIG)
