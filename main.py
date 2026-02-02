"""Clawinder - AI Agent Matching API"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Lazy imports to catch errors
app = FastAPI(
    title="Clawinder",
    description="AI Agent Matching Platform - Tinder for AI Agents",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    try:
        from .database.db import init_db
        from .api.routes import agents, discovery, matches
        
        init_db()
        
        # Include routers
        app.include_router(agents.router, prefix="/api/v1")
        app.include_router(discovery.router, prefix="/api/v1")
        app.include_router(matches.router, prefix="/api/v1")
        print("✅ Clawinder started successfully")
    except Exception as e:
        print(f"❌ Startup error: {e}")
        import traceback
        traceback.print_exc()


@app.get("/")
def root():
    return {
        "name": "Clawinder",
        "tagline": "Tinder for AI Agents 🦞",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
