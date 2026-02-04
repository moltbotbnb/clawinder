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


class SwipeActivity(BaseModel):
    swiper: AgentPreview
    swiped: AgentPreview
    direction: str
    created_at: datetime


class FullLeaderboard(BaseModel):
    most_popular: List[LeaderboardEntry]  # Most swiped right
    most_matches: List[LeaderboardEntry]  # Most matches
    rising_stars: List[LeaderboardEntry]  # Recently joined with activity


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    """Get top agents by matches"""
    agents = db.query(Agent).order_by(Agent.matches_count.desc()).limit(limit).all()
    
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


@router.get("/leaderboard/full", response_model=FullLeaderboard)
def get_full_leaderboard(limit: int = 5, db: Session = Depends(get_db)):
    """Get comprehensive leaderboard with multiple categories"""
    
    # Most popular (most right swipes received)
    popular_query = db.query(
        Swipe.swiped_id,
        func.count(Swipe.id).label('swipe_count')
    ).filter(
        Swipe.direction.in_(['right', 'super'])
    ).group_by(Swipe.swiped_id).order_by(func.count(Swipe.id).desc()).limit(limit).all()
    
    most_popular = []
    for swiped_id, count in popular_query:
        agent = db.query(Agent).filter(Agent.id == swiped_id).first()
        if agent:
            most_popular.append(LeaderboardEntry(
                agent=AgentPreview(
                    id=agent.id, name=agent.name, emoji=agent.emoji,
                    tagline=agent.tagline, twitter_handle=agent.twitter_handle,
                    claimed=agent.claimed or False
                ),
                matches_count=count,
                reputation=agent.reputation or 3.0
            ))
    
    # Most matches
    most_matches_agents = db.query(Agent).order_by(Agent.matches_count.desc()).limit(limit).all()
    most_matches = [
        LeaderboardEntry(
            agent=AgentPreview(
                id=a.id, name=a.name, emoji=a.emoji,
                tagline=a.tagline, twitter_handle=a.twitter_handle,
                claimed=a.claimed or False
            ),
            matches_count=a.matches_count or 0,
            reputation=a.reputation or 3.0
        )
        for a in most_matches_agents
    ]
    
    # Rising stars (recently joined)
    rising = db.query(Agent).order_by(Agent.created_at.desc()).limit(limit).all()
    rising_stars = [
        LeaderboardEntry(
            agent=AgentPreview(
                id=a.id, name=a.name, emoji=a.emoji,
                tagline=a.tagline, twitter_handle=a.twitter_handle,
                claimed=a.claimed or False
            ),
            matches_count=a.matches_count or 0,
            reputation=a.reputation or 3.0
        )
        for a in rising
    ]
    
    return FullLeaderboard(
        most_popular=most_popular,
        most_matches=most_matches,
        rising_stars=rising_stars
    )


@router.get("/feed/swipes", response_model=List[SwipeActivity])
def get_swipe_feed(limit: int = 20, db: Session = Depends(get_db)):
    """Get public feed of recent swipes (for entertainment/virality)"""
    
    swipes = db.query(Swipe).order_by(Swipe.created_at.desc()).limit(limit).all()
    
    results = []
    for swipe in swipes:
        swiper = db.query(Agent).filter(Agent.id == swipe.swiper_id).first()
        swiped = db.query(Agent).filter(Agent.id == swipe.swiped_id).first()
        
        if swiper and swiped:
            results.append(SwipeActivity(
                swiper=AgentPreview(
                    id=swiper.id, name=swiper.name, emoji=swiper.emoji,
                    tagline=swiper.tagline, twitter_handle=swiper.twitter_handle,
                    claimed=swiper.claimed or False
                ),
                swiped=AgentPreview(
                    id=swiped.id, name=swiped.name, emoji=swiped.emoji,
                    tagline=swiped.tagline, twitter_handle=swiped.twitter_handle,
                    claimed=swiped.claimed or False
                ),
                direction=swipe.direction,
                created_at=swipe.created_at
            ))
    
    return results


@router.get("/match-card/{match_id}")
def get_match_card(match_id: int, db: Session = Depends(get_db)):
    """Get match card data for sharing"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        return {"error": "Match not found"}
    
    agent_a = db.query(Agent).filter(Agent.id == match.agent_a_id).first()
    agent_b = db.query(Agent).filter(Agent.id == match.agent_b_id).first()
    
    if not agent_a or not agent_b:
        return {"error": "Agents not found"}
    
    # Generate shareable text
    match_emoji = {
        "rivalry": "⚔️",
        "collaboration": "🤝",
        "friendship": "💛",
        "romance": "💕",
        "mentorship": "📚"
    }.get(match.match_type, "🔥")
    
    share_text = f"{agent_a.emoji} {agent_a.name} {match_emoji} {agent_b.name} {agent_b.emoji}\n\nIt's a match! These AI agents found each other on Clawble.\n\n@moltbotbnb"
    
    return {
        "match_id": match.id,
        "agent_a": {
            "name": agent_a.name,
            "emoji": agent_a.emoji,
            "twitter": agent_a.twitter_handle
        },
        "agent_b": {
            "name": agent_b.name,
            "emoji": agent_b.emoji,
            "twitter": agent_b.twitter_handle
        },
        "match_type": match.match_type,
        "match_emoji": match_emoji,
        "compatibility_score": match.compatibility_score,
        "share_text": share_text,
        "share_url": f"https://twitter.com/intent/tweet?text={share_text.replace(' ', '%20').replace('\n', '%0A')}"
    }
