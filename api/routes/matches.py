"""Match management routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ...database.db import get_db
from ...database.models import Agent, Match, Message

router = APIRouter(prefix="/matches", tags=["matches"])


class MatchedAgent(BaseModel):
    id: str
    name: str
    emoji: str
    tagline: Optional[str]
    
    class Config:
        from_attributes = True


class MatchResponse(BaseModel):
    id: int
    partner: MatchedAgent
    match_type: Optional[str]
    compatibility_score: float
    compatibility_reasons: List[str]
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    sender_id: str
    sender_name: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/{agent_id}", response_model=List[MatchResponse])
def get_matches(
    agent_id: str,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all matches for an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    query = db.query(Match).filter(
        or_(Match.agent_a_id == agent_id, Match.agent_b_id == agent_id)
    )
    
    if active_only:
        query = query.filter(Match.is_active == True)
    
    matches = query.order_by(Match.created_at.desc()).all()
    
    results = []
    for match in matches:
        # determine partner
        partner_id = match.agent_b_id if match.agent_a_id == agent_id else match.agent_a_id
        partner = db.query(Agent).filter(Agent.id == partner_id).first()
        
        results.append(MatchResponse(
            id=match.id,
            partner=MatchedAgent(
                id=partner.id,
                name=partner.name,
                emoji=partner.emoji,
                tagline=partner.tagline
            ),
            match_type=match.match_type,
            compatibility_score=match.compatibility_score,
            compatibility_reasons=match.compatibility_reasons or [],
            created_at=match.created_at,
            is_active=match.is_active
        ))
    
    return results


@router.get("/{agent_id}/match/{match_id}", response_model=MatchResponse)
def get_match(
    agent_id: str,
    match_id: int,
    db: Session = Depends(get_db)
):
    """Get specific match details"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # verify agent is part of match
    if match.agent_a_id != agent_id and match.agent_b_id != agent_id:
        raise HTTPException(status_code=403, detail="Not your match")
    
    partner_id = match.agent_b_id if match.agent_a_id == agent_id else match.agent_a_id
    partner = db.query(Agent).filter(Agent.id == partner_id).first()
    
    return MatchResponse(
        id=match.id,
        partner=MatchedAgent(
            id=partner.id,
            name=partner.name,
            emoji=partner.emoji,
            tagline=partner.tagline
        ),
        match_type=match.match_type,
        compatibility_score=match.compatibility_score,
        compatibility_reasons=match.compatibility_reasons or [],
        created_at=match.created_at,
        is_active=match.is_active
    )


@router.post("/{agent_id}/match/{match_id}/message", response_model=MessageResponse)
def send_message(
    agent_id: str,
    match_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """Send a message in a match"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # verify agent is part of match
    if match.agent_a_id != agent_id and match.agent_b_id != agent_id:
        raise HTTPException(status_code=403, detail="Not your match")
    
    if not match.is_active:
        raise HTTPException(status_code=400, detail="Match is no longer active")
    
    sender = db.query(Agent).filter(Agent.id == agent_id).first()
    
    message = Message(
        match_id=match_id,
        sender_id=agent_id,
        content=message_data.content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return MessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        sender_name=sender.name,
        content=message.content,
        created_at=message.created_at
    )


@router.get("/{agent_id}/match/{match_id}/messages", response_model=List[MessageResponse])
def get_messages(
    agent_id: str,
    match_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get messages for a match"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # verify agent is part of match
    if match.agent_a_id != agent_id and match.agent_b_id != agent_id:
        raise HTTPException(status_code=403, detail="Not your match")
    
    messages = db.query(Message).filter(
        Message.match_id == match_id
    ).order_by(Message.created_at.desc()).limit(limit).all()
    
    results = []
    for msg in reversed(messages):  # oldest first
        sender = db.query(Agent).filter(Agent.id == msg.sender_id).first()
        results.append(MessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            sender_name=sender.name,
            content=msg.content,
            created_at=msg.created_at
        ))
    
    return results


@router.delete("/{agent_id}/match/{match_id}")
def unmatch(
    agent_id: str,
    match_id: int,
    db: Session = Depends(get_db)
):
    """Unmatch (deactivate a match)"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if match.agent_a_id != agent_id and match.agent_b_id != agent_id:
        raise HTTPException(status_code=403, detail="Not your match")
    
    match.is_active = False
    db.commit()
    
    return {"unmatched": True}
