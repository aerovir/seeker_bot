"""
Seeker Bot — FastAPI application.

Provides REST API for TMA and health check endpoint.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common.logging import logger
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    logger.info("api_starting")
    yield
    logger.info("api_stopping")


app = FastAPI(
    title="Seeker Bot API",
    description="REST API for Seeker Bot Telegram Mini App",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.tma_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "seeker-bot-api",
        "version": "0.1.0",
    }
