# backend/app/main.py
from fastapi import FastAPI
from app.routes import router

app = FastAPI(
    title="WhatsApp Chat Analyzer API",
    description="Upload chat and get insights",
    version="1.0.0"
)

app.include_router(router)
