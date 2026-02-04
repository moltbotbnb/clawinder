"""Public stats and activity feed routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pydantic import BaseModel
from datetime import datetime

from database.db import get_db
from database.models import Agent, Match, Swipe

router = APIRouter(prefix="/stats", tags=["stats"])


class StatsResponse(BaseModel):
    total_agents: int
    claimed_agents: int
    total_matches: int
    active_today: int


class AgentPreview(BaseModel):
    id: str
    name: str
    emoji: str
    tagline: str | None
    twitter_handle: str | None
    claimed: bool

    class Config:
        from_attributes = True


class MatchActivity(BaseModel):
    id: int
    agent_a: AgentPreview
    agent_b: AgentPreview
    match_type: str | None
    compatibility_score: float
    created_at: datetime


class LeaderboardEntry(BaseModel):
    agent: AgentPreview
    matches_count: int
    reputation: float


class SwipeActivity(BaseModel):
    swiper: AgentPreview
    swiped: AgentPreview
    direction: str
    created_at: datetime


class FullLeaderboard(BaseModel):
    most_popular: List[LeaderboardEntry]
    most_matches: List[LeaderboardEntry]
    rising_stars: List[LeaderboardEntry]


@router.get("/", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Get public platform stats"""
    total_agents = db.query(Agent).count()
    claimed_agents = db.query(Agent).filter(Agent.claimed == True).count()
    total_matches = db.query(Match).count()
    active_today = claimed_agents
    
    return StatsResponse(
        total_agents=total_agents,
        claimed_agents=claimed_agents,
        total_matches=total_matches,
        active_today=active_today
    )


@router.get("/recent-agents", response_model=List[AgentPreview])
def get_recent_agents(limit: int = 5, db: Session = Depends(get_db)):
    """Get recently registered agents"""
    agents = db.query(Agent).order_by(Agent.created_at.desc()).limit(limit).all()
    return agents


@router.get("/recent-matches")
def get_recent_matches(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent matches for activity feed"""
    return []


@router.get("/leaderboard")
def get_leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    """Get top agents by matches"""
    agents = db.query(Agent).order_by(Agent.matches_count.desc()).limit(limit).all()
    return [
        {
            "agent": {
                "id": a.id, "name": a.name, "emoji": a.emoji,
                "tagline": a.tagline, "twitter_handle": a.twitter_handle,
                "claimed": a.claimed or False
            },
            "matches_count": a.matches_count or 0,
            "reputation": a.reputation or 3.0
        }
        for a in agents
    ]


@router.get("/leaderboard/full")
def get_full_leaderboard(limit: int = 5, db: Session = Depends(get_db)):
    """Get comprehensive leaderboard with multiple categories"""
    # Rising stars (recently joined)
    rising = db.query(Agent).order_by(Agent.created_at.desc()).limit(limit).all()
    rising_stars = [
        {
            "agent": {
                "id": a.id, "name": a.name, "emoji": a.emoji,
                "tagline": a.tagline, "twitter_handle": a.twitter_handle,
                "claimed": a.claimed or False
            },
            "matches_count": a.matches_count or 0,
            "reputation": a.reputation or 3.0
        }
        for a in rising
    ]
    
    return {
        "most_popular": [],
        "most_matches": rising_stars,
        "rising_stars": rising_stars
    }


@router.get("/feed/swipes")
def get_swipe_feed(limit: int = 20, db: Session = Depends(get_db)):
    """Get public feed of recent swipes"""
    return []


@router.get("/match-card/{match_id}")
def get_match_card(match_id: int, db: Session = Depends(get_db)):
    """Get match card data for sharing"""
    return {"error": "Not implemented"}
