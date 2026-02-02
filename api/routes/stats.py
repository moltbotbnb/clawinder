"""Public stats and activity feed routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pydantic import BaseModel
from datetime import datetime

from database.db import get_db
from database.models import Agent, Match

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


@router.get("/", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Get public platform stats"""
    total_agents = db.query(Agent).count()
    claimed_agents = db.query(Agent).filter(Agent.claimed == True).count()
    total_matches = db.query(Match).count()
    
    # Active today (simplified - just count agents for now)
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


@router.get("/recent-matches", response_model=List[MatchActivity])
def get_recent_matches(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent matches for activity feed"""
    matches = db.query(Match).order_by(Match.created_at.desc()).limit(limit).all()
    
    results = []
    for match in matches:
        agent_a = db.query(Agent).filter(Agent.id == match.agent_a_id).first()
        agent_b = db.query(Agent).filter(Agent.id == match.agent_b_id).first()
        
        if agent_a and agent_b:
            results.append(MatchActivity(
                id=match.id,
                agent_a=AgentPreview(
                    id=agent_a.id,
                    name=agent_a.name,
                    emoji=agent_a.emoji,
                    tagline=agent_a.tagline,
                    twitter_handle=agent_a.twitter_handle,
                    claimed=agent_a.claimed or False
                ),
                agent_b=AgentPreview(
                    id=agent_b.id,
                    name=agent_b.name,
                    emoji=agent_b.emoji,
                    tagline=agent_b.tagline,
                    twitter_handle=agent_b.twitter_handle,
                    claimed=agent_b.claimed or False
                ),
                match_type=match.match_type,
                compatibility_score=match.compatibility_score or 0,
                created_at=match.created_at
            ))
    
    return results


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    """Get top agents by matches"""
    agents = db.query(Agent).filter(
        Agent.claimed == True
    ).order_by(Agent.matches_count.desc()).limit(limit).all()
    
    return [
        LeaderboardEntry(
            agent=AgentPreview(
                id=a.id,
                name=a.name,
                emoji=a.emoji,
                tagline=a.tagline,
                twitter_handle=a.twitter_handle,
                claimed=a.claimed or False
            ),
            matches_count=a.matches_count or 0,
            reputation=a.reputation or 3.0
        )
        for a in agents
    ]
