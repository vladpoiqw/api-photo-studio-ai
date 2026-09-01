import os

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "AI Photo Studio API работает"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
