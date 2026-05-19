"""
CIRO — FastAPI Application Entry Point
========================================
Bootstraps the async FastAPI server with CORS, health checks,
router registration, and startup data ingestion.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import signals, crises, resources, simulations
from app.api import traces
from app.core.middleware import add_error_handling_middleware
from app.services.ingestion import seed_startup_data


# ── Lifespan ────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    await seed_startup_data()
    yield


# ── App ─────────────────────────────────────────
app = FastAPI(
    title="CIRO — Crisis Intelligence & Response Orchestrator",
    description="Agentic backend for real-time metropolitan crisis management.",
    version="0.1.0",
    lifespan=lifespan,
)

add_error_handling_middleware(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────
app.include_router(signals.router, prefix="/api/v1/signals", tags=["Signals"])
app.include_router(crises.router, prefix="/api/v1/crises", tags=["Crises"])
app.include_router(resources.router, prefix="/api/v1/resources", tags=["Resources"])
app.include_router(simulations.router, prefix="/api/v1/simulations", tags=["Simulations"])
app.include_router(traces.router, prefix="/api/v1/traces", tags=["Traces"])

# Direct ingestion route mapping for Phase 2 spec compatibility
@app.post("/api/v1/ingest", tags=["Signals"], status_code=201, summary="Direct ingest endpoint")
async def direct_ingest(signal: signals.IngestedSignal, background_tasks: signals.BackgroundTasks):
    return await signals.ingest_signal(signal, background_tasks)


# ── Health ──────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "ciro-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
