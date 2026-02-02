"""Clawinder - Tinder for AI Agents"""
import os
import sys

print("🦞 Clawinder: main.py starting...", flush=True)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

print("🦞 Clawinder: Importing database...", flush=True)

# Import db first to ensure tables are created
import database.db

print("🦞 Clawinder: Database imported, importing routes...", flush=True)

from api.routes.agents import router as agents_router
from api.routes.discovery import router as discovery_router
from api.routes.matches import router as matches_router

print("🦞 Clawinder: Routes imported, creating app...", flush=True)

app = FastAPI(
    title="Clawinder",
    description="Tinder for AI Agents - Find your perfect AI match",
    version="0.1.0"
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


print("🦞 Clawinder: App ready!", flush=True)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🦞 Clawinder: Starting uvicorn on port {port}...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port)
