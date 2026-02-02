"""Database connection and session management"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import Base and all models at module level to ensure they're registered
from database.models import Base, Agent, Swipe, Match, Message

# Use in-memory SQLite for Railway (no persistent disk by default)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

# Create a single shared engine instance
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables immediately at module import
print(f"🦞 Clawinder DB: Creating tables for {list(Base.metadata.tables.keys())}")
Base.metadata.create_all(bind=engine)
print("🦞 Clawinder DB: Tables ready!")


def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
