import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./xdmra.db")


def _normalize_postgresql_url(url: str) -> str:
    if url.startswith("postgresql+psycopg://") or url.startswith("postgres+psycopg://"):
        return url
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1).replace("postgres://", "postgres+psycopg://", 1)
    return url


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def _is_postgresql(url: str) -> bool:
    return url.startswith("postgresql") or url.startswith("postgres")


def _create_engine_args(url: str) -> dict:
    if _is_sqlite(url):
        return {"connect_args": {"check_same_thread": False}}
    elif _is_postgresql(url):
        return {"pool_pre_ping": True}
    return {}


_normalized_url = _normalize_postgresql_url(DATABASE_URL)
engine_kwargs = _create_engine_args(_normalized_url)
engine = create_engine(_normalized_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()