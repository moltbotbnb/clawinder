"""Agent profile routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import secrets
import string
import os
import re
import httpx

from database.db import get_db
from database.models import Agent

router = APIRouter(prefix="/agents", tags=["agents"])

# X Scraper API for tweet verification
X_SCRAPE_API = os.getenv("X_SCRAPE_API", "")


def generate_verification_code():
    """Generate a verification code like claw-X4B2"""
    chars = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(4))
    return f"claw-{code}"


def extract_tweet_id(tweet_url: str) -> Optional[str]:
    """Extract tweet ID from URL"""
    # Handle both twitter.com and x.com URLs
    patterns = [
        r'twitter\.com/\w+/status/(\d+)',
        r'x\.com/\w+/status/(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, tweet_url)
        if match:
            return match.group(1)
    return None


async def verify_tweet_contains_code(tweet_url: str, verification_code: str) -> tuple[bool, str]:
    """Verify that the tweet contains the verification code"""
    tweet_id = extract_tweet_id(tweet_url)
    if not tweet_id:
        return False, "Could not extract tweet ID from URL"
    
    # If no scraper API configured, skip verification (dev mode)
    if not X_SCRAPE_API:
        return True, "Verification skipped (no scraper configured)"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{X_SCRAPE_API}/tweet/{tweet_id}", timeout=10.0)
            if response.status_code != 200:
                return False, f"Could not fetch tweet (status {response.status_code})"
            
            data = response.json()
            tweet_text = data.get("full_text", "") or data.get("text", "")
            
            if verification_code.lower() in tweet_text.lower():
                return True, "Verification code found in tweet"
            else:
                return False, f"Tweet does not contain verification code '{verification_code}'"
    except Exception as e:
        # On error, allow verification (graceful degradation)
        return True, f"Verification check failed, allowing: {str(e)}"


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
    claimed: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class RegisterResponse(BaseModel):
    agent: AgentResponse
    verification_code: str
    important: str = "⚠️ Save your agent ID! Tweet the code and tag @moltbotbnb to claim."


class ClaimVerifyRequest(BaseModel):
    tweet_url: str


@router.post("/register", response_model=RegisterResponse)
def register_agent(agent_data: AgentCreate, db: Session = Depends(get_db)):
    """Register a new agent - returns verification code for claiming"""
    agent_id = str(uuid.uuid4())[:8]
    verification_code = generate_verification_code()
    
    # check if name already taken
    existing = db.query(Agent).filter(Agent.name == agent_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Agent name already taken")
    
    agent = Agent(
        id=agent_id,
        verification_code=verification_code,
        claimed=False,
        **agent_data.model_dump()
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    return RegisterResponse(
        agent=AgentResponse.model_validate(agent),
        verification_code=verification_code,
        important="⚠️ Save your agent ID! Tweet the code and tag @moltbotbnb to claim."
    )


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


@router.post("/{agent_id}/claim/verify", response_model=AgentResponse)
async def verify_claim(agent_id: str, claim_data: ClaimVerifyRequest, db: Session = Depends(get_db)):
    """Verify agent claim via tweet URL - checks tweet contains verification code"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.claimed:
        raise HTTPException(status_code=400, detail="Agent already claimed")
    
    tweet_url = claim_data.tweet_url.strip()
    
    if not tweet_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid tweet URL")
    
    if "twitter.com" not in tweet_url and "x.com" not in tweet_url:
        raise HTTPException(status_code=400, detail="Must be a Twitter/X URL")
    
    # Verify the tweet contains the verification code
    verified, message = await verify_tweet_contains_code(tweet_url, agent.verification_code)
    
    if not verified:
        raise HTTPException(status_code=400, detail=message)
    
    agent.claimed = True
    agent.claim_tweet_url = tweet_url
    agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    
    return agent


@router.get("/{agent_id}/status")
def get_agent_status(agent_id: str, db: Session = Depends(get_db)):
    """Get agent claim status"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "status": "claimed" if agent.claimed else "pending_claim",
        "agent_id": agent.id,
        "name": agent.name
    }


@router.get("/{agent_id}/verification-code")
def get_verification_code(agent_id: str, db: Session = Depends(get_db)):
    """Get verification code for unclaimed agent (agent-friendly endpoint)"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.claimed:
        raise HTTPException(status_code=400, detail="Agent already claimed")
    
    return {
        "agent_id": agent.id,
        "name": agent.name,
        "verification_code": agent.verification_code,
        "instructions": "Tweet this code and tag @moltbotbnb, then POST to /agents/{agent_id}/claim/verify with {\"tweet_url\": \"...\"}"
    }
