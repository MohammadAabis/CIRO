"""Simulations API — run and retrieve what-if scenario results."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.store import store

router = APIRouter()


@router.get("/", summary="List simulation outcomes")
async def list_simulations(crisis_id: Optional[UUID] = Query(None)):
    sims = await store.get_simulations(crisis_id=crisis_id)
    return {
        "count": len(sims),
        "simulations": [s.model_dump(mode="json") for s in sims],
    }


@router.get("/{simulation_id}", summary="Get simulation outcome")
async def get_simulation(simulation_id: UUID):
    sim = await store.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(404, f"Simulation {simulation_id} not found")
    return sim.model_dump(mode="json")
