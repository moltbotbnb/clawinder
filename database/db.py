"""Database session management"""
import sys

# Import from package to use shared engine/sessionmaker/base
from database import engine, SessionLocal, Base
from database.models import Agent, Swipe, Match, Message

def init_db():
    """Create all tables"""
    print(f"🦞 Clawble: Creating tables {list(Base.metadata.tables.keys())}", flush=True)
    Base.metadata.create_all(bind=engine)
    print("🦞 Clawble: Tables ready!", flush=True)

def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize tables on import
print("🦞 Clawble: db.py loading, calling init_db()...", flush=True)
init_db()
print("🦞 Clawble: db.py loaded!", flush=True)
