import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import core, analytics, predictions, supply, price_index, scenarios, events, graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from datetime import datetime

scheduler = BackgroundScheduler()

def ping_self():
    """Background task to ping the health endpoint preventing Render spin-down."""
    port = os.getenv("PORT", "8000")
    url = f"http://127.0.0.1:{port}/health"
    try:
        # Fire-and-forget synchronous HTTP request for the scheduler 
        with httpx.Client() as client:
            client.get(url, timeout=5.0)
            logger.info(f"Self-ping executed successfully bound to {url}")
    except Exception as e:
        logger.warning(f"Self-ping failed gracefully natively: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.add_job(ping_self, 'interval', minutes=10)
    scheduler.start()
    logger.info("APScheduler initialized background self-pings.")
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(
    title="BorAnalytics API",
    description="Backend API for BorAnalytics Global Boron Trade ML Dashboard",
    version="1.0.0",
    lifespan=lifespan
)

from config import settings

# CORS configuration for defined frontend domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include endpoint routers
app.include_router(core.router, tags=["Core"])
app.include_router(analytics.router, tags=["Analytics"])
app.include_router(predictions.router, tags=["Predictions"])
app.include_router(supply.router)
app.include_router(price_index.router)
app.include_router(scenarios.router)
app.include_router(events.router, prefix='/api', tags=['events'])
app.include_router(graph.router, prefix='/api', tags=['graph'])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to BorAnalytics API"}

@app.get("/health")
def health_check():
    """Lightweight endpoint confirming structural availability globally."""
    return {"status": "ok", "version": "v4", "timestamp": datetime.utcnow().isoformat()}
