"""
Database connection setup.

Everything here is driven by the DATABASE_URL environment variable.
For local dev, .env points at your local Postgres install on localhost:5432.
For production (e.g. Render), you'll just set DATABASE_URL in Render's
dashboard to Render's own Postgres connection string — nothing in this
file or api.py needs to change.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()  # reads variables from your .env file into the environment

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Add it to your .env file, e.g.\n"
        "DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/founders_forge"
    )

# pool_pre_ping=True checks connections are alive before using them —
# prevents mysterious errors if the DB restarts while your app is running.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency: gives each request its own DB session,
    and always closes it afterwards, even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()