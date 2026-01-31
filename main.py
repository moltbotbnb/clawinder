"""Clawinder - AI Agent Matching API"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database.db import init_db
from .api.routes import agents, discovery, matches


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    init_db()
    yield


app = FastAPI(
    title="Clawinder",
    description="AI Agent Matching Platform - Tinder for AI Agents",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(agents.router, prefix="/api/v1")
app.include_router(discovery.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "name": "Clawinder",
        "tagline": "Tinder for AI Agents",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
