import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://monitor:monitor@localhost:5432/monitor")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)


def get_session() -> Session:
    return SessionLocal()
