"""Signals API — ingest and retrieve raw crisis signals."""

from fastapi import APIRouter, Query, BackgroundTasks
from app.schemas import IngestedSignal
from app.store import store
from app.agents.orchestrator import run_orchestrator_pipeline

router = APIRouter()


@router.post("/", status_code=201, summary="Ingest a new signal")
async def ingest_signal(signal: IngestedSignal, background_tasks: BackgroundTasks) -> dict:
    saved = await store.add_signal(signal)
    # Trigger multi-agent pipeline in background
    background_tasks.add_task(run_orchestrator_pipeline, saved)
    return {"status": "ingested", "signal_id": str(saved.id)}


@router.get("/", summary="List recent signals")
async def list_signals(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    signals = await store.get_signals(limit=limit, offset=offset)
    return {
        "count": len(signals),
        "total": len(store.signals),
        "signals": [s.model_dump(mode="json") for s in signals],
    }
