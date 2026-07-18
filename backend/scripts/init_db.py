"""
Database initialization script for production deployment.

Creates all required tables without seeding demo data.
Safe to run on existing databases - does not modify existing data.

Usage:
    python -m scripts.init_db

Or from backend directory:
    python -m scripts.init_db
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base

def init_db():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")

if __name__ == "__main__":
    init_db()