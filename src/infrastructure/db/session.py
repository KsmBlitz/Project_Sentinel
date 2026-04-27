import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://monitor:monitor@localhost:5432/monitor")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)


def get_session() -> Session:
    return SessionLocal()
