import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import core, analytics, predictions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BorAnalytics API",
    description="Backend API for BorAnalytics Global Boron Trade ML Dashboard",
    version="1.0.0"
)

# CORS configuration for local React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include endpoint routers
app.include_router(core.router, tags=["Core"])
app.include_router(analytics.router, tags=["Analytics"])
app.include_router(predictions.router, tags=["Predictions"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to BorAnalytics API"}
