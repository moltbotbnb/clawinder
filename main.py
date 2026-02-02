"""Clawinder - Minimal"""
import os
from fastapi import FastAPI

app = FastAPI(title="Clawinder")

@app.get("/")
def root():
    return {"name": "Clawinder", "status": "alive", "port": os.getenv("PORT", "unknown")}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
