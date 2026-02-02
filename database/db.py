"""Database connection and session management"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use in-memory SQLite for Railway (no persistent disk by default)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

# Create a single shared engine instance
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables"""
    # Import models here to ensure they're registered with Base
    from database.models import Base, Agent, Swipe, Match, Message
    print(f"🦞 Initializing database tables... (url: {DATABASE_URL})")
    print(f"🦞 Tables to create: {list(Base.metadata.tables.keys())}")
    Base.metadata.create_all(bind=engine)
    print("🦞 Database tables created!")


def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
