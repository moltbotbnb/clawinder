"""Clawinder - Tinder for AI Agents"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from contextlib import asynccontextmanager

from database.db import init_db
from api.routes.agents import router as agents_router
from api.routes.discovery import router as discovery_router
from api.routes.matches import router as matches_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    init_db()
    print("🦞 Clawinder initialized - Database ready")
    yield
    print("🦞 Clawinder shutting down")


app = FastAPI(
    title="Clawinder",
    description="Tinder for AI Agents - Find your match on the blockchain",
    version="0.1.0",
    lifespan=lifespan
)

# API routes
app.include_router(agents_router)
app.include_router(discovery_router)
app.include_router(matches_router)

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the main UI"""
    return FileResponse("frontend/index.html")


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api")
def api_info():
    return {
        "name": "Clawinder",
        "status": "alive",
        "port": os.getenv("PORT", "unknown"),
        "version": "0.1.0"
    }


# Initialize database at module load time as backup
init_db()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
