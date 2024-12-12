from typing import Iterator

from sqlmodel import create_engine, SQLModel, Session

from app.core.config import settings

connect_args = {"check_same_thread": False}
engine = create_engine(
    "sqlite:///" + settings.SQLITE_DB, echo=True, connect_args=connect_args
)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)
