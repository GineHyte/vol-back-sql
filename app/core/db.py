from typing import Iterator

from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy import event

from app.core.config import settings

connect_args = {"check_same_thread": False}
engine = create_engine(
    "sqlite:///" + settings.SQLITE_DB, echo=False, connect_args=connect_args
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Ensure PRAGMA foreign_keys=ON is set for new connections
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)
