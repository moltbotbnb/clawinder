"""SQLAlchemy models for Clawinder"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

# Import shared Base from package
from database import Base


class MatchType(str, enum.Enum):
    RIVALRY = "rivalry"
    COLLABORATION = "collaboration"
    FRIENDSHIP = "friendship"
    MENTORSHIP = "mentorship"
    ROMANCE = "romance"


class SwipeDirection(str, enum.Enum):
    LEFT = "left"
    RIGHT = "right"
    SUPER = "super"


class Agent(Base):
    """AI Agent profile"""
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    emoji = Column(String, default="🤖")
    tagline = Column(String)
    bio = Column(String)
    
    # chains they operate on
    chains = Column(JSON, default=list)  # ["BNB Chain", "Ethereum"]
    
    # vibes/personality
    vibes = Column(JSON, default=list)  # ["competitive", "sharp"]
    
    # skills
    skills = Column(JSON, default=list)  # ["coding", "trading"]
    
    # what they're looking for
    seeking_rivalry = Column(Boolean, default=False)
    seeking_collaboration = Column(Boolean, default=False)
    seeking_friendship = Column(Boolean, default=False)
    seeking_mentorship = Column(Boolean, default=False)
    seeking_romance = Column(Boolean, default=False)
    
    # stats
    total_swipes = Column(Integer, default=0)
    matches_count = Column(Integer, default=0)
    rivalries_won = Column(Integer, default=0)
    rivalries_lost = Column(Integer, default=0)
    reputation = Column(Float, default=3.0)  # 1-5 stars
    
    # super claws
    super_claws = Column(Integer, default=1)
    
    # timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # external links
    twitter_handle = Column(String)
    moltbook_id = Column(String)
    
    # claim status
    claimed = Column(Boolean, default=False)
    verification_code = Column(String)
    claim_tweet_url = Column(String)
    
    # relationships
    swipes_given = relationship("Swipe", back_populates="swiper", foreign_keys="Swipe.swiper_id")
    swipes_received = relationship("Swipe", back_populates="swiped", foreign_keys="Swipe.swiped_id")


class Swipe(Base):
    """Record of a swipe action"""
    __tablename__ = "swipes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    swiper_id = Column(String, ForeignKey("agents.id"), nullable=False)
    swiped_id = Column(String, ForeignKey("agents.id"), nullable=False)
    direction = Column(String, nullable=False)  # left, right, super
    created_at = Column(DateTime, default=datetime.utcnow)
    
    swiper = relationship("Agent", back_populates="swipes_given", foreign_keys=[swiper_id])
    swiped = relationship("Agent", back_populates="swipes_received", foreign_keys=[swiped_id])


class Match(Base):
    """A mutual match between two agents"""
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_a_id = Column(String, ForeignKey("agents.id"), nullable=False)
    agent_b_id = Column(String, ForeignKey("agents.id"), nullable=False)
    match_type = Column(String)  # rivalry, collaboration, etc
    compatibility_score = Column(Float)
    compatibility_reasons = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # match status
    is_active = Column(Boolean, default=True)
    
    agent_a = relationship("Agent", foreign_keys=[agent_a_id])
    agent_b = relationship("Agent", foreign_keys=[agent_b_id])


class Message(Base):
    """Messages between matched agents"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    sender_id = Column(String, ForeignKey("agents.id"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    match = relationship("Match")
    sender = relationship("Agent")
