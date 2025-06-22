from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, delete, col 

from app.core.db import engine, get_session
from app.data.db import CoachSession
from app.core.logger import logger


def _remove_expired_sessions():
    """Remove expired sessions."""
    current_time = int(datetime.now().timestamp())
    session = next(get_session())
    session.exec(delete(CoachSession).where(col(CoachSession.expires_at) < current_time))
    session.commit()


def start_scheduler():
    logger.info("Starting scheduler for removing expired sessions")
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _remove_expired_sessions, "interval", seconds=10
    )
    scheduler.start()
