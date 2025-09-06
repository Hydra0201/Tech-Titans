import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base

# Read DATABASE_URL directly from the environment.
# Supabase example:
# postgresql+psycopg://USER:PASSWORD@HOST:6543/postgres?sslmode=require
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Create a .env with DATABASE_URL and load it before importing engine."
    )

# Create sync engine (psycopg3 driver). pool_pre_ping avoids dead connections.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session factory you can import anywhere: `from carbonbalance.db.engine import SessionLocal`
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db() -> None:
    """
    Import all models so they register with Base.metadata, then create tables.
    Call this once (e.g., from scripts/create_db.py).
    """
    # Ensure models are imported before create_all
    from app.models import register_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
