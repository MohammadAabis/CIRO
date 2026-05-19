"""Crises API — crisis state CRUD and analytics."""

from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from app.store import store

router = APIRouter()


@router.get("/", summary="List active crises")
async def list_crises(active_only: bool = Query(True)):
    crises = await store.get_crises(active_only=active_only)
    return {
        "count": len(crises),
        "crises": [c.model_dump(mode="json") for c in crises],
    }


@router.get("/stats", summary="Dashboard statistics")
async def dashboard_stats():
    return await store.dashboard_stats()


@router.get("/{crisis_id}", summary="Get crisis detail")
async def get_crisis(crisis_id: UUID):
    crisis = await store.get_crisis(crisis_id)
    if not crisis:
        raise HTTPException(404, f"Crisis {crisis_id} not found")
    return crisis.model_dump(mode="json")
