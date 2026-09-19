"""
Shared SQLAlchemy engine/session setup. Both core-api and safety-service
import models from here, but each connects using ITS OWN role's
credentials (see backend/db/grants.sql) — this file does not hardcode
which role is used, that's decided by DATABASE_URL at runtime per service.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://localhost/campus_connect"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
