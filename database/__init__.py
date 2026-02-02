"""Database package - initialize on import"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

# Single shared engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Single shared Base
Base = declarative_base()
