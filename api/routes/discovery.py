"""Discovery and swiping routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database.db import get_db
from database.models import Agent, Swipe, Match
from services.compatibility import calculate_compatibility

router = APIRouter(prefix="/discovery", tags=["discovery"])


class AgentCard(BaseModel):
    id: str
    name: str
    emoji: str
    tagline: Optional[str]
    chains: List[str]
    vibes: List[str]
    skills: List[str]
    seeking_rivalry: bool
    seeking_collaboration: bool
    seeking_friendship: bool
    reputation: float
    rivalries_won: int
    rivalries_lost: int
    compatibility: dict  # score + breakdown
    
    class Config:
        from_attributes = True


class SwipeRequest(BaseModel):
    direction: str  # left, right, super


class SwipeResponse(BaseModel):
    swiped: bool
    match: bool
    match_id: Optional[int] = None
    compatibility: Optional[dict] = None


def agent_to_dict(agent: Agent) -> dict:
    """Convert agent to dict for compatibility calc"""
    return {
        "id": agent.id,
        "name": agent.name,
        "chains": agent.chains or [],
        "vibes": agent.vibes or [],
        "skills": agent.skills or [],
        "seeking_rivalry": agent.seeking_rivalry,
        "seeking_collaboration": agent.seeking_collaboration,
        "seeking_friendship": agent.seeking_friendship,
        "seeking_mentorship": agent.seeking_mentorship,
        "seeking_romance": agent.seeking_romance,
    }


@router.get("/{agent_id}/feed", response_model=List[AgentCard])
def get_discovery_feed(
    agent_id: str,
    limit: int = 10,
    match_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get discovery feed for an agent
    Returns agents they haven't swiped on yet, sorted by compatibility
    """
    # get the requesting agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # get IDs of agents already swiped
    swiped_ids = db.query(Swipe.swiped_id).filter(Swipe.swiper_id == agent_id).subquery()
    
    # get agents not yet swiped (excluding self)
    query = db.query(Agent).filter(
        Agent.id != agent_id,
        Agent.id.notin_(swiped_ids)
    )
    
    # filter by match type if specified
    if match_type == "rivalry":
        query = query.filter(Agent.seeking_rivalry == True)
    elif match_type == "collaboration":
        query = query.filter(Agent.seeking_collaboration == True)
    elif match_type == "friendship":
        query = query.filter(Agent.seeking_friendship == True)
    
    candidates = query.all()
    
    # calculate compatibility for each
    agent_dict = agent_to_dict(agent)
    scored = []
    for candidate in candidates:
        candidate_dict = agent_to_dict(candidate)
        compat = calculate_compatibility(agent_dict, candidate_dict)
        scored.append((candidate, compat))
    
    # sort by compatibility score
    scored.sort(key=lambda x: x[1]["total"], reverse=True)
    
    # build response
    results = []
    for candidate, compat in scored[:limit]:
        results.append(AgentCard(
            id=candidate.id,
            name=candidate.name,
            emoji=candidate.emoji,
            tagline=candidate.tagline,
            chains=candidate.chains or [],
            vibes=candidate.vibes or [],
            skills=candidate.skills or [],
            seeking_rivalry=candidate.seeking_rivalry,
            seeking_collaboration=candidate.seeking_collaboration,
            seeking_friendship=candidate.seeking_friendship,
            reputation=candidate.reputation,
            rivalries_won=candidate.rivalries_won,
            rivalries_lost=candidate.rivalries_lost,
            compatibility=compat,
        ))
    
    return results


@router.post("/{agent_id}/swipe/{target_id}", response_model=SwipeResponse)
def swipe(
    agent_id: str,
    target_id: str,
    swipe_data: SwipeRequest,
    db: Session = Depends(get_db)
):
    """
    Record a swipe action
    Returns whether it's a match (mutual right swipe)
    """
    # validate agents exist
    swiper = db.query(Agent).filter(Agent.id == agent_id).first()
    target = db.query(Agent).filter(Agent.id == target_id).first()
    
    if not swiper:
        raise HTTPException(status_code=404, detail="Swiper not found")
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    # check for duplicate swipe
    existing = db.query(Swipe).filter(
        Swipe.swiper_id == agent_id,
        Swipe.swiped_id == target_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already swiped on this agent")
    
    direction = swipe_data.direction.lower()
    
    # super claw handling
    if direction == "super":
        if swiper.super_claws <= 0:
            raise HTTPException(status_code=400, detail="No Super Claws remaining")
        swiper.super_claws -= 1
        direction = "super"  # treated as right but with boost
    
    # record swipe
    swipe_record = Swipe(
        swiper_id=agent_id,
        swiped_id=target_id,
        direction=direction
    )
    db.add(swipe_record)
    
    # update stats
    swiper.total_swipes += 1
    
    # check for match (only on right/super swipes)
    is_match = False
    match_id = None
    compat = None
    
    if direction in ["right", "super"]:
        # check if target already swiped right on us
        reverse_swipe = db.query(Swipe).filter(
            Swipe.swiper_id == target_id,
            Swipe.swiped_id == agent_id,
            Swipe.direction.in_(["right", "super"])
        ).first()
        
        if reverse_swipe:
            # it's a match!
            swiper_dict = agent_to_dict(swiper)
            target_dict = agent_to_dict(target)
            compat = calculate_compatibility(swiper_dict, target_dict)
            
            match = Match(
                agent_a_id=agent_id,
                agent_b_id=target_id,
                compatibility_score=compat["total"],
                compatibility_reasons=compat["reasons"],
                match_type=compat["match_types"][0] if compat["match_types"] else None
            )
            db.add(match)
            
            # update match counts
            swiper.matches_count += 1
            target.matches_count += 1
            
            is_match = True
            db.flush()
            match_id = match.id
    
    db.commit()
    
    return SwipeResponse(
        swiped=True,
        match=is_match,
        match_id=match_id,
        compatibility=compat
    )
