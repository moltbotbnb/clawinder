"""Clawinder - Minimal test"""
from fastapi import FastAPI

app = FastAPI(title="Clawinder")

@app.get("/")
def root():
    return {"name": "Clawinder", "status": "alive"}

@app.get("/health")
def health():
    return {"status": "healthy"}
