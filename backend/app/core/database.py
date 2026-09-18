from collections.abc import Generator

from sqlmodel import Session, create_engine

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def create_session() -> Session:
    """Create a new database session."""

    return Session(engine)
