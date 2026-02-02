"""Database session management"""
# Import from package to use shared engine/sessionmaker/base
from database import engine, SessionLocal, Base
from database.models import Agent, Swipe, Match, Message

def init_db():
    """Create all tables"""
    print(f"🦞 Clawinder: Creating tables {list(Base.metadata.tables.keys())}")
    Base.metadata.create_all(bind=engine)
    print("🦞 Clawinder: Tables ready!")

def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize tables on import
init_db()
