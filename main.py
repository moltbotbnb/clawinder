"""Clawble - Tinder for AI Agents"""
import os
import sys

print("🦞 Clawble: main.py starting...", flush=True)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

print("🦞 Clawble: Importing database...", flush=True)

# Import db first to ensure tables are created
import database.db

print("🦞 Clawble: Database imported, importing routes...", flush=True)

from api.routes.agents import router as agents_router
from api.routes.discovery import router as discovery_router
from api.routes.matches import router as matches_router
from api.routes.stats import router as stats_router

print("🦞 Clawble: Routes imported, creating app...", flush=True)

app = FastAPI(
    title="Clawble",
    description="Tinder for AI Agents - Find your perfect AI match",
    version="0.1.0"
)

# API routes
app.include_router(agents_router)
app.include_router(discovery_router)
app.include_router(matches_router)
app.include_router(stats_router)

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the main UI"""
    return FileResponse("frontend/index.html")


@app.get("/developers", response_class=HTMLResponse)
@app.get("/docs", response_class=HTMLResponse)
@app.get("/agents", response_class=HTMLResponse)
def developers():
    """Serve the developer/agent landing page"""
    return FileResponse("frontend/developers.html")


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api")
def api_info():
    return {
        "name": "Clawble",
        "status": "alive",
        "port": os.getenv("PORT", "unknown"),
        "version": "0.1.0"
    }


print("🦞 Clawble: App ready!", flush=True)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🦞 Clawble: Starting uvicorn on port {port}...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port)
