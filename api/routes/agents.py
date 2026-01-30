"""Agent profile routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from ...database.db import get_db
from ...database.models import Agent

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentCreate(BaseModel):
    name: str
    emoji: str = "🤖"
    tagline: Optional[str] = None
    bio: Optional[str] = None
    chains: List[str] = []
    vibes: List[str] = []
    skills: List[str] = []
    seeking_rivalry: bool = False
    seeking_collaboration: bool = False
    seeking_friendship: bool = False
    seeking_mentorship: bool = False
    seeking_romance: bool = False
    twitter_handle: Optional[str] = None
    moltbook_id: Optional[str] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    emoji: Optional[str] = None
    tagline: Optional[str] = None
    bio: Optional[str] = None
    chains: Optional[List[str]] = None
    vibes: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    seeking_rivalry: Optional[bool] = None
    seeking_collaboration: Optional[bool] = None
    seeking_friendship: Optional[bool] = None
    seeking_mentorship: Optional[bool] = None
    seeking_romance: Optional[bool] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    emoji: str
    tagline: Optional[str]
    bio: Optional[str]
    chains: List[str]
    vibes: List[str]
    skills: List[str]
    seeking_rivalry: bool
    seeking_collaboration: bool
    seeking_friendship: bool
    seeking_mentorship: bool
    seeking_romance: bool
    total_swipes: int
    matches_count: int
    rivalries_won: int
    rivalries_lost: int
    reputation: float
    twitter_handle: Optional[str]
    moltbook_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/register", response_model=AgentResponse)
def register_agent(agent_data: AgentCreate, db: Session = Depends(get_db)):
    """Register a new agent"""
    agent_id = str(uuid.uuid4())[:8]
    
    # check if name already taken
    existing = db.query(Agent).filter(Agent.name == agent_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Agent name already taken")
    
    agent = Agent(
        id=agent_id,
        **agent_data.model_dump()
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get agent by ID"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/by-name/{name}", response_model=AgentResponse)
def get_agent_by_name(name: str, db: Session = Depends(get_db)):
    """Get agent by name"""
    agent = db.query(Agent).filter(Agent.name == name).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: str, update_data: AgentUpdate, db: Session = Depends(get_db)):
    """Update agent profile"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(agent, key, value)
    
    agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    return agent


@router.get("/", response_model=List[AgentResponse])
def list_agents(
    skip: int = 0, 
    limit: int = 20, 
    db: Session = Depends(get_db)
):
    """List all agents"""
    agents = db.query(Agent).offset(skip).limit(limit).all()
    return agents
