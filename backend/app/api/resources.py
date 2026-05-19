"""Resources API — emergency resource inventory management."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.store import store

router = APIRouter()


class StatusUpdate(BaseModel):
    status: str
    assigned_crisis_id: Optional[UUID] = None


@router.get("/", summary="Get resource inventory snapshot")
async def get_inventory():
    inv = await store.get_inventory()
    return {
        "snapshot_time": inv.snapshot_time.isoformat(),
        "jurisdiction": inv.jurisdiction,
        "total_units": len(inv.units),
        "summary": inv.summary,
        "units": [u.model_dump(mode="json") for u in inv.units],
    }


@router.patch("/{unit_id}/status", summary="Update unit status")
async def update_unit_status(unit_id: UUID, body: StatusUpdate):
    unit = await store.update_unit_status(
        unit_id, body.status, body.assigned_crisis_id
    )
    if not unit:
        raise HTTPException(404, f"Unit {unit_id} not found")
    return {"updated": True, "unit": unit.model_dump(mode="json")}
