"""
AI-Powered Engineer Service Desk — FastAPI Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, SessionLocal
from app.services.seed_service import seed_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize DB and seed on startup."""
    logger.info("Starting Engineer Service Desk...")
    init_db()
    logger.info("Database tables created/verified.")

    # Seed dataset (idempotent — skips if already seeded)
    db = SessionLocal()
    try:
        seed_database(db)
    except Exception as e:
        logger.error("Seed failed: %s — application will start with empty/partial data.", str(e))
    finally:
        db.close()

    logger.info("Service Desk ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Engineer Service Desk",
    description="AI-Powered Engineer Service Desk Console",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers
from app.routers import dashboard, tickets, comments, ai, knowledge_base, agents

app.include_router(dashboard.router)
app.include_router(tickets.router)
app.include_router(comments.router)
app.include_router(ai.router)
app.include_router(knowledge_base.router)
app.include_router(agents.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Engineer Service Desk"}
