"""
CIRO In-Memory Data Store
===========================
Thread-safe, async-compatible in-memory state for all domain objects.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.schemas import (
    IngestedSignal, CrisisState, ResourceInventory, ResourceUnit,
    SimulationOutcome, TraceEntry, TraceLog,
)


class CiroStore:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.signals: dict[UUID, IngestedSignal] = {}
        self.crises: dict[UUID, CrisisState] = {}
        self.simulations: dict[UUID, SimulationOutcome] = {}
        self.trace_logs: dict[UUID, TraceLog] = {}
        self.resource_inventory = ResourceInventory()
        self._trace_subs: list[asyncio.Queue[TraceEntry]] = []

    # ── Signals ─────────────────────────────────
    async def add_signal(self, signal: IngestedSignal) -> IngestedSignal:
        async with self._lock:
            self.signals[signal.id] = signal
        return signal

    async def get_signals(self, limit: int = 50, offset: int = 0) -> list[IngestedSignal]:
        items = sorted(self.signals.values(), key=lambda s: s.timestamp, reverse=True)
        return items[offset:offset + limit]

    # ── Crises ──────────────────────────────────
    async def upsert_crisis(self, crisis: CrisisState) -> CrisisState:
        async with self._lock:
            crisis.updated_at = datetime.utcnow()
            self.crises[crisis.id] = crisis
        return crisis

    async def get_crises(self, active_only: bool = True) -> list[CrisisState]:
        items = list(self.crises.values())
        if active_only:
            items = [c for c in items if not c.is_false_alarm]
        return sorted(items, key=lambda c: c.severity.value, reverse=True)

    async def get_crisis(self, crisis_id: UUID) -> Optional[CrisisState]:
        return self.crises.get(crisis_id)

    # ── Resources ───────────────────────────────
    async def set_inventory(self, inv: ResourceInventory) -> None:
        async with self._lock:
            self.resource_inventory = inv

    async def get_inventory(self) -> ResourceInventory:
        return self.resource_inventory

    async def update_unit_status(self, unit_id: UUID, status: str,
                                  assigned_crisis_id: Optional[UUID] = None) -> Optional[ResourceUnit]:
        async with self._lock:
            for unit in self.resource_inventory.units:
                if unit.id == unit_id:
                    unit.status = status
                    if assigned_crisis_id is not None:
                        unit.assigned_crisis_id = assigned_crisis_id
                    return unit
        return None

    # ── Simulations ─────────────────────────────
    async def add_simulation(self, sim: SimulationOutcome) -> SimulationOutcome:
        async with self._lock:
            self.simulations[sim.id] = sim
        return sim

    async def get_simulations(self, crisis_id: Optional[UUID] = None) -> list[SimulationOutcome]:
        items = list(self.simulations.values())
        if crisis_id:
            items = [s for s in items if s.crisis_id == crisis_id]
        return sorted(items, key=lambda s: s.run_at, reverse=True)

    async def get_simulation(self, sim_id: UUID) -> Optional[SimulationOutcome]:
        return self.simulations.get(sim_id)

    # ── Traces (with SSE fan-out) ───────────────
    async def add_trace_log(self, trace: TraceLog) -> TraceLog:
        async with self._lock:
            self.trace_logs[trace.pipeline_run_id] = trace
        return trace

    async def append_trace_entry(self, pipeline_run_id: UUID, entry: TraceEntry) -> None:
        async with self._lock:
            log = self.trace_logs.get(pipeline_run_id)
            if log:
                log.entries.append(entry)
            for q in self._trace_subs:
                try:
                    q.put_nowait(entry)
                except asyncio.QueueFull:
                    pass

    def subscribe_traces(self) -> asyncio.Queue[TraceEntry]:
        q: asyncio.Queue[TraceEntry] = asyncio.Queue(maxsize=256)
        self._trace_subs.append(q)
        return q

    def unsubscribe_traces(self, q: asyncio.Queue[TraceEntry]) -> None:
        self._trace_subs = [s for s in self._trace_subs if s is not q]

    async def get_trace_logs(self) -> list[TraceLog]:
        return sorted(self.trace_logs.values(), key=lambda t: t.started_at, reverse=True)

    # ── Dashboard Stats ─────────────────────────
    async def dashboard_stats(self) -> dict:
        inv = self.resource_inventory
        return {
            "total_signals": len(self.signals),
            "active_crises": len([c for c in self.crises.values() if not c.is_false_alarm]),
            "false_alarms": len([c for c in self.crises.values() if c.is_false_alarm]),
            "total_simulations": len(self.simulations),
            "resources": {"total": len(inv.units), "available": len(inv.available),
                          "deployed": len(inv.deployed), "summary": inv.summary},
        }


# Singleton
store = CiroStore()
