"""
CIRO Agentic Orchestration Engine
===================================
Uses Google GenAI / Gemini API to process signals through a multi-agent
pipeline (Signal Fusion → Crisis Classifier → Resource Allocator → Impact Simulator).

Maintains a global TraceLogger and updates the in-memory store.
Supports both real Gemini API (via GOOGLE_API_KEY) and a high-fidelity
fallback engine for offline/dummy hackathon environments.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Union
from uuid import UUID, uuid4

from google.api_core import exceptions as google_exceptions
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings
from app.schemas import (
    CrisisState, CrisisType, EvolutionaryPath, EvolutionTrend,
    GeoLocation, IngestedSignal, ResourceInventory, ResourceStatus,
    ResourceType, ResourceUnit, Severity, SideEffect,
    SimulationOutcome, SignalSource, StateSnapshot,
    TraceEntry, TraceLog, TrafficData, WeatherMetrics,
)
from app.store import store

# Setup logger
logger = logging.getLogger("ciro.orchestrator")
logger.setLevel(logging.INFO)

GEMINI_DEGRADED_ERRORS = (
    google_exceptions.GoogleAPICallError,
    google_exceptions.RetryError,
    google_exceptions.ResourceExhausted,
    google_exceptions.TooManyRequests,
    google_exceptions.ServiceUnavailable,
    google_exceptions.DeadlineExceeded,
    ValidationError,
    json.JSONDecodeError,
    TimeoutError,
)


def _to_naive_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts
    return ts.astimezone(timezone.utc).replace(tzinfo=None)


def _normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return " ".join(text.lower().split())


def _location_signature(location: Optional[GeoLocation]) -> tuple[Optional[float], Optional[float], Optional[str]]:
    if not location:
        return None, None, None
    label = (location.label or "").strip().lower() or None
    return round(location.latitude, 3), round(location.longitude, 3), label


def _filter_stale_signals(signals: list[IngestedSignal], max_age_minutes: int) -> tuple[list[IngestedSignal], list[IngestedSignal]]:
    if max_age_minutes <= 0:
        return signals, []
    now = datetime.utcnow()
    max_age = timedelta(minutes=max_age_minutes)
    fresh: list[IngestedSignal] = []
    stale: list[IngestedSignal] = []
    for sig in signals:
        if now - _to_naive_utc(sig.timestamp) > max_age:
            stale.append(sig)
        else:
            fresh.append(sig)
    return fresh, stale


def _deduplicate_signals(signals: list[IngestedSignal], window_seconds: int) -> tuple[list[IngestedSignal], list[IngestedSignal]]:
    if window_seconds <= 0:
        return signals, []
    window = timedelta(seconds=window_seconds)
    kept: list[IngestedSignal] = []
    dropped: list[IngestedSignal] = []
    for sig in sorted(signals, key=lambda s: s.timestamp, reverse=True):
        sig_key = (sig.source, _normalize_text(sig.raw_text), _location_signature(sig.location))
        is_dup = False
        for prev in kept:
            prev_key = (prev.source, _normalize_text(prev.raw_text), _location_signature(prev.location))
            if prev_key != sig_key:
                continue
            if abs(_to_naive_utc(prev.timestamp) - _to_naive_utc(sig.timestamp)) <= window:
                is_dup = True
                break
        if is_dup:
            dropped.append(sig)
        else:
            kept.append(sig)
    return kept, dropped


def _prepare_signals_for_fusion(ctx: PipelineContext, signals: list[IngestedSignal]) -> list[IngestedSignal]:
    start_time = datetime.utcnow()
    fresh, stale = _filter_stale_signals(signals, settings.SIGNAL_MAX_AGE_MINUTES)
    deduped, duplicates = _deduplicate_signals(fresh, settings.SIGNAL_DEDUP_WINDOW_SECONDS)
    if stale or duplicates:
        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        ctx.log_step(
            "SignalFusionAgent",
            "deduplicate",
            f"Received {len(signals)} raw signals.",
            f"Dropped {len(duplicates)} duplicates and {len(stale)} stale signals. {len(deduped)} retained.",
            duration,
            {
                "dedup_window_seconds": settings.SIGNAL_DEDUP_WINDOW_SECONDS,
                "max_age_minutes": settings.SIGNAL_MAX_AGE_MINUTES,
            },
        )
    return deduped


# ──────────────────────────────────────────────
# Pydantic Schemas for Schema-Enforced Gemini API
# ──────────────────────────────────────────────

class FusedSignalGroup(BaseModel):
    signals_analyzed: list[str] = Field(..., description="IDs of signals analyzed")
    fused_location: GeoLocation = Field(..., description="Estimated centroid/location")
    source_credibility: float = Field(..., description="Fused credibility score (0 to 1)")
    geolocation_confidence: float = Field(..., description="Confidence in geolocation accuracy (0 to 1)")
    has_contradictions: bool = Field(..., description="True if conflicting reports exist")
    contradiction_details: Optional[str] = Field(None, description="Details of contradiction")
    resolution_path: Optional[str] = Field(None, description="Resolution taken/proposed")
    is_infrastructure_failure: bool = Field(..., description="True if burst pipe/infrastructure rather than flood")
    confidence_score: float = Field(..., description="Overall fusion confidence score")


class CrisisClassification(BaseModel):
    crisis_type: CrisisType
    title: str = Field(..., description="Title of the crisis")
    description: str = Field(..., description="Full summary")
    severity: Severity = Field(..., description="Severity 1 to 5")
    confidence: float = Field(..., description="Classification confidence (0 to 1)")
    affected_population: int = Field(..., description="Estimated affected population")
    expected_duration_hours: float = Field(..., description="Expected duration in hours")
    is_false_alarm: bool = Field(..., description="Is this a false alarm / reclassified event?")
    false_alarm_reason: Optional[str] = Field(None)


class ResourceAllocationProposal(BaseModel):
    allocated_units: list[str] = Field(..., description="Call-signs of allocated units")
    trade_off_log: str = Field(..., description="Detailed trade-off reasoning")
    response_delay_impact: str = Field(..., description="Delay and bottleneck details")


class SimulationResult(BaseModel):
    before_state: StateSnapshot
    after_state: StateSnapshot
    side_effects: list[SideEffect]
    overall_effectiveness: float = Field(..., description="Effectiveness index (0 to 1)")
    public_alert: str = Field(..., description="Tailored public advisory / retraction alert")
    hospital_alert: str = Field(..., description="Direct alert for local emergency rooms")
    utility_alert: str = Field(..., description="Operational warning for water/power utilities")
    recommendation: str = Field(..., description="Actionable recommendation")


# ──────────────────────────────────────────────
# Global Pipeline Run Context
# ──────────────────────────────────────────────

class PipelineContext:
    def __init__(self, target_signal: IngestedSignal) -> None:
        self.run_id = uuid4()
        self.started_at = datetime.utcnow()
        self.target_signal = target_signal
        self.trace_entries: list[TraceEntry] = []

    def log_step(self, agent_name: str, action: str, inp: str, out: str, duration_ms: int, meta: Optional[dict] = None) -> TraceEntry:
        entry = TraceEntry(
            timestamp=datetime.utcnow(),
            agent_name=agent_name,
            action=action,
            input_summary=inp,
            output_summary=out,
            duration_ms=duration_ms,
            metadata=meta or {},
        )
        self.trace_entries.append(entry)
        # Dispatch to live SSE listeners via store
        asyncio.create_task(store.append_trace_entry(self.run_id, entry))
        return entry

    def get_log(self, crisis_id: Optional[UUID] = None) -> TraceLog:
        return TraceLog(
            pipeline_run_id=self.run_id,
            crisis_id=crisis_id,
            started_at=self.started_at,
            entries=self.trace_entries,
        )


# ──────────────────────────────────────────────
# Fallback Engine (High-Fidelity Simulated Agents)
# ──────────────────────────────────────────────

class FallbackPipeline:
    """
    Generates deterministic, highly realistic responses for hackathon scenarios.
    Invoked when GOOGLE_API_KEY is dummy or absent.
    """

    @staticmethod
    async def run_signal_fusion(ctx: PipelineContext, all_signals: list[IngestedSignal]) -> FusedSignalGroup:
        start_time = datetime.utcnow()
        await asyncio.sleep(0.5)  # Simulate network latency

        # Check if we have the water main report or IoT sensor in the signals
        has_water_main = any("water main" in (s.raw_text or "").lower() for s in all_signals)
        has_iot_pressure = any("pressure drop" in (s.raw_text or "").lower() for s in all_signals)

        if has_water_main or has_iot_pressure:
            fused = FusedSignalGroup(
                signals_analyzed=[str(s.id) for s in all_signals],
                fused_location=GeoLocation(latitude=33.6840, longitude=73.0490, label="7th Ave / G-10 junction"),
                source_credibility=0.88,
                geolocation_confidence=0.95,
                has_contradictions=True,
                contradiction_details="Social media reported massive flooding; field report claims water main burst. IoT sensor shows G-10 line pressure dropped to 12 PSI.",
                resolution_path="Resolving conflict in favour of official citizen field report and hardware IoT telemetry. Reclassifying flash flood as infrastructure pipe break.",
                is_infrastructure_failure=True,
                confidence_score=0.91,
            )
        elif any("heatwave" in (s.raw_text or "").lower() or "heat stroke" in (s.raw_text or "").lower() for s in all_signals):
            fused = FusedSignalGroup(
                signals_analyzed=[str(s.id) for s in all_signals],
                fused_location=GeoLocation(latitude=33.7060, longitude=73.0551, label="F-8/3, Islamabad"),
                source_credibility=0.92,
                geolocation_confidence=0.90,
                has_contradictions=False,
                is_infrastructure_failure=False,
                confidence_score=0.95,
            )
        else:
            fused = FusedSignalGroup(
                signals_analyzed=[str(s.id) for s in all_signals],
                fused_location=GeoLocation(latitude=33.6844, longitude=73.0479, label="G-10/4, Islamabad"),
                source_credibility=0.65,
                geolocation_confidence=0.85,
                has_contradictions=False,
                is_infrastructure_failure=False,
                confidence_score=0.80,
            )

        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        ctx.log_step(
            "SignalFusionAgent", "fuse_multisource_signals",
            f"Fusing {len(all_signals)} active raw signal inputs.",
            f"Fuzed centroid: {fused.fused_location.label}. Contradiction found: {fused.has_contradictions}.",
            duration,
            {"is_fallback": True}
        )
        return fused

    @staticmethod
    async def run_crisis_classification(ctx: PipelineContext, fused: FusedSignalGroup) -> CrisisClassification:
        start_time = datetime.utcnow()
        await asyncio.sleep(0.4)

        if fused.is_infrastructure_failure:
            cls_out = CrisisClassification(
                crisis_type=CrisisType.INFRASTRUCTURE_FAILURE,
                title="Broken Water Main — G-10 Islamabad (RECLASSIFIED)",
                description="Massive water pooling previously reported as flash flooding has been confirmed as a primary water main pipe burst on 7th Avenue. Retracting weather alerts.",
                severity=Severity.MODERATE,
                confidence=0.92,
                affected_population=2000,
                expected_duration_hours=4.0,
                is_false_alarm=True,
                false_alarm_reason="Water main burst telemetry (12 PSI) and field reports confirmed this is a localised infrastructure burst, NOT a meteorological flash flood. Retracted weather warning.",
            )
        elif fused.fused_location.latitude > 33.7:  # F-8 region
            cls_out = CrisisClassification(
                crisis_type=CrisisType.HEATWAVE,
                title="Extreme Heatwave — F-8 Islamabad",
                description="Dangerous heatwave with temperatures reaching 47°C (heat index 52°C). High risk of medical emergencies. Critical resource strain.",
                severity=Severity.SIGNIFICANT,
                confidence=0.95,
                affected_population=25000,
                expected_duration_hours=14.0,
                is_false_alarm=False,
            )
        else:
            cls_out = CrisisClassification(
                crisis_type=CrisisType.URBAN_FLOOD,
                title="Urban Flooding — G-10 Islamabad",
                description="Severe storm and drainage blockage causing urban flooding in Sector G-10. Main market and low-lying residential sectors impacted.",
                severity=Severity.SEVERE,
                confidence=0.87,
                affected_population=12000,
                expected_duration_hours=8.0,
                is_false_alarm=False,
            )

        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        ctx.log_step(
            "CrisisClassifier", "classify_crisis_state",
            f"Fused Group Confidence: {fused.confidence_score}. Coordinates: ({fused.fused_location.latitude}, {fused.fused_location.longitude})",
            f"Classified: {cls_out.title} | Severity: {cls_out.severity.value}/5 | False Alarm: {cls_out.is_false_alarm}",
            duration,
            {"is_fallback": True}
        )
        return cls_out

    @staticmethod
    async def run_resource_allocation(ctx: PipelineContext, cls_out: CrisisClassification, inventory: ResourceInventory) -> ResourceAllocationProposal:
        start_time = datetime.utcnow()
        await asyncio.sleep(0.6)

        available_units = [u for u in inventory.units if u.status == ResourceStatus.AVAILABLE]
        allocated = []

        if cls_out.is_false_alarm:
            # We release/retract all rescue units. No ambulances needed, just deploy 1 police unit to manage traffic near broken main.
            police = [u for u in available_units if u.resource_type == ResourceType.POLICE]
            if police:
                allocated.append(police[0].call_sign)
            proposal = ResourceAllocationProposal(
                allocated_units=allocated,
                trade_off_log="Retracted all flood rescue units (ambulances and rescue teams) originally destined for G-10. Dispatched 1 police unit for local traffic control while CDA utility repair crew fixes the pipe.",
                response_delay_impact="None. High-capacity rescue assets immediately returned to the ready pool.",
            )
        elif cls_out.crisis_type == CrisisType.HEATWAVE:
            # Allocate ambulances and medical staff
            amb = [u for u in available_units if u.resource_type == ResourceType.AMBULANCE]
            med = [u for u in available_units if u.resource_type == ResourceType.MEDICAL_STAFF]
            allocated.extend([u.call_sign for u in amb[:3]])
            allocated.extend([u.call_sign for u in med[:2]])
            proposal = ResourceAllocationProposal(
                allocated_units=allocated,
                trade_off_log="Allocating 3 ambulances and 2 medical units to F-8 heat cooling centres. Trade-off: Leaving remaining medical staff in reserve to cover ongoing flash flood emergencies in G-10.",
                response_delay_impact="Moderate risk: F-8 Markaz is congested. Expected response delay 8-12 minutes.",
            )
        else:
            # Flood allocation
            rsc = [u for u in available_units if u.resource_type == ResourceType.RESCUE_TEAM]
            amb = [u for u in available_units if u.resource_type == ResourceType.AMBULANCE]
            evb = [u for u in available_units if u.resource_type == ResourceType.EVACUATION_BUS]
            allocated.extend([u.call_sign for u in rsc[:3]])
            allocated.extend([u.call_sign for u in amb[:2]])
            allocated.extend([u.call_sign for u in evb[:1]])
            proposal = ResourceAllocationProposal(
                allocated_units=allocated,
                trade_off_log="Deployed 3 rescue teams, 2 ambulances, and 1 evacuation bus to G-10. Diverting rescue units from neighboring sectors to cover the G-10 flashpoint.",
                response_delay_impact="Low delay. G-10 access roads are open but congested.",
            )

        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        ctx.log_step(
            "ResourceAllocator", "solve_constrained_allocation",
            f"Crisis: {cls_out.title} | Available Fleet: {len(available_units)} units",
            f"Allocated: {allocated}. Trade-offs: {proposal.trade_off_log[:100]}...",
            duration,
            {"is_fallback": True}
        )
        return proposal

    @staticmethod
    async def run_impact_simulation(ctx: PipelineContext, cls_out: CrisisClassification, proposal: ResourceAllocationProposal) -> SimulationResult:
        start_time = datetime.utcnow()
        await asyncio.sleep(0.5)

        if cls_out.is_false_alarm:
            sim = SimulationResult(
                before_state=StateSnapshot(
                    severity=Severity.MODERATE, affected_population=2000, infrastructure_damage_pct=15.0,
                    casualties_estimate=0, economic_impact_usd=150000,
                    narrative="Flooding warning causes panic, unnecessary evacuation, and gridlock."
                ),
                after_state=StateSnapshot(
                    severity=Severity.MINOR, affected_population=500, infrastructure_damage_pct=5.0,
                    casualties_estimate=0, economic_impact_usd=30000,
                    narrative="Emergency alerts retracted. Public informed of water supply main failure. Utility repairs in progress."
                ),
                side_effects=[],
                overall_effectiveness=0.95,
                public_alert="RETRACTION: The flash flood warning for Sector G-10 has been cancelled. Flooding was caused by a burst water main on 7th Ave which is being repaired by CDA crews. No evacuation required.",
                hospital_alert="NOTICE: Retract trauma surge alerts for G-10 sector. Standard operating conditions resumed.",
                utility_alert="ACTION REQUIRED: Water supply isolated on Sector G-10 feeder. Proceed with line pressure bypass and clamp installation.",
                recommendation="RETRACT ALL PUBLIC FLOOD WARNINGS. Broadcast water main repairs update to citizen dashboards.",
            )
        elif cls_out.crisis_type == CrisisType.HEATWAVE:
            sim = SimulationResult(
                before_state=StateSnapshot(
                    severity=Severity.SEVERE, affected_population=25000, infrastructure_damage_pct=0.0,
                    casualties_estimate=8, economic_impact_usd=200000,
                    narrative="Unchecked heatstroke cases overwhelm ER admissions; high casualties among elderly."
                ),
                after_state=StateSnapshot(
                    severity=Severity.MODERATE, affected_population=12000, infrastructure_damage_pct=0.0,
                    casualties_estimate=1, economic_impact_usd=80000,
                    narrative="Cooling centres hydrate 5000 citizens. On-site medics stabilise heatstroke cases."
                ),
                side_effects=[
                    SideEffect(description="Cooling station high-amp power generators draw load from neighborhood grid", probability=0.35, impact_severity=Severity.MINOR)
                ],
                overall_effectiveness=0.82,
                public_alert="ALERT: Extreme heat warning for Sector F-8. 47°C. Avoid outdoor activity. 4 hydration/cooling stations set up at F-8 Markaz and Sector Park.",
                hospital_alert="ALERT: ER trauma capacity warned for extreme hyperthermia admissions. Diverting non-critical patients to surrounding sectors.",
                utility_alert="NOTICE: Peak power demand forecasted. Cooperate with IESCO to prevent local transformer overload.",
                recommendation="DEPLOY HYDRATION CAMPAIGN. Keep residents indoors via cell broadcast.",
            )
        else:
            sim = SimulationResult(
                before_state=StateSnapshot(
                    severity=Severity.CATASTROPHIC, affected_population=12000, infrastructure_damage_pct=35.0,
                    casualties_estimate=12, economic_impact_usd=2500000,
                    narrative="Water reaches +80cm in G-10 residential areas. 150 basements flooded."
                ),
                after_state=StateSnapshot(
                    severity=Severity.SIGNIFICANT, affected_population=8000, infrastructure_damage_pct=15.0,
                    casualties_estimate=2, economic_impact_usd=900000,
                    narrative="Evacuation bus removes 400 vulnerable citizens. Rescue crews extract stranded vehicles. Drains pumped."
                ),
                side_effects=[
                    SideEffect(description="Khayaban-e-Suharwardy closed to commercial traffic for emergency vehicle staging", probability=0.8, impact_severity=Severity.MINOR)
                ],
                overall_effectiveness=0.75,
                public_alert="CRITICAL ALERT: Flash flooding in Sector G-10. Avoid low-lying areas. Emergency assembly point established at G-10 sector school.",
                hospital_alert="ALERT: G-10 medical clinics evacuated. Prepare PIMS to accept flood transfer casualties.",
                utility_alert="ALERT: CDA water supply lines and local electrical grids shut down in flooded G-10 blocks to prevent electrocution.",
                recommendation="IMMEDIATE EVACUATION of G-10/4 basements. Secure electrical transformers.",
            )

        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        ctx.log_step(
            "SimulationAgent", "predict_response_outcomes",
            f"Crisis: {cls_out.title} | Response Action: {proposal.allocated_units}",
            f"Mitigation index: {sim.overall_effectiveness}. Side Effects count: {len(sim.side_effects)}.",
            duration,
            {"is_fallback": True}
        )
        return sim


# ──────────────────────────────────────────────
# Google GenAI / Gemini API Integration
# ──────────────────────────────────────────────

class GenaiPipeline:
    """
    Executes the multi-agent pipeline using real schema-enforced Gemini API calls.
    """

    @staticmethod
    def _get_client():
        from google import genai
        return genai.Client(api_key=settings.GOOGLE_API_KEY)

    @classmethod
    async def run_signal_fusion(cls, ctx: PipelineContext, all_signals: list[IngestedSignal]) -> FusedSignalGroup:
        start_time = datetime.utcnow()
        client = cls._get_client()

        signals_json = json.dumps([s.model_dump(mode="json") for s in all_signals])
        prompt = f"""
        Act as the Signal Fusion Agent.
        Analyze these raw signals and combine them:
        {signals_json}

        Determine the combined location, credibility score, and identify any contradictions.
        Pay critical attention: If there is a field report or water main pressure drop, flag it as a burst pipe / infrastructure failure (set is_infrastructure_failure to true) and describe the contradiction.
        """

        # Call Gemini using loop executor (Gemini SDK is synchronous, so run in executor)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": FusedSignalGroup,
                }
            )
        )

        fused = FusedSignalGroup.model_validate_json(response.text)
        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        ctx.log_step(
            "SignalFusionAgent", "fuse_multisource_signals",
            f"Fusing {len(all_signals)} active raw signal inputs.",
            f"Fuzed centroid: {fused.fused_location.label}. Contradiction found: {fused.has_contradictions}.",
            duration,
            {"model": settings.GEMINI_MODEL}
        )
        return fused

    @classmethod
    async def run_crisis_classification(cls, ctx: PipelineContext, fused: FusedSignalGroup) -> CrisisClassification:
        start_time = datetime.utcnow()
        client = cls._get_client()

        prompt = f"""
        Act as the Crisis Classifier Agent.
        Evaluate this fused signal group and produce a structured crisis classification:
        {fused.model_dump_json()}

        If is_infrastructure_failure is true, classify it as a false alarm / infrastructure reclassification (is_false_alarm = true) and explain the false alarm reason.
        """

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": CrisisClassification,
                }
            )
        )

        cls_out = CrisisClassification.model_validate_json(response.text)
        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        ctx.log_step(
            "CrisisClassifier", "classify_crisis_state",
            f"Fused Group Confidence: {fused.confidence_score}. Coordinates: ({fused.fused_location.latitude}, {fused.fused_location.longitude})",
            f"Classified: {cls_out.title} | Severity: {cls_out.severity.value}/5 | False Alarm: {cls_out.is_false_alarm}",
            duration,
            {"model": settings.GEMINI_MODEL}
        )
        return cls_out

    @classmethod
    async def run_resource_allocation(cls, ctx: PipelineContext, cls_out: CrisisClassification, inventory: ResourceInventory) -> ResourceAllocationProposal:
        start_time = datetime.utcnow()
        client = cls._get_client()

        prompt = f"""
        Act as the Resource Allocator Agent.
        Find an optimal allocation of these available emergency resources:
        {inventory.model_dump_json()}

        For this classified crisis:
        {cls_out.model_dump_json()}

        Rules:
        - If the crisis is a false alarm / retracted, withdraw all heavy rescue teams/ambulances, and only allocate 1-2 police/local repair units.
        - Minimize response delay and log detailed trade-off reasons (especially if multiple crises are active).
        """

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": ResourceAllocationProposal,
                }
            )
        )

        proposal = ResourceAllocationProposal.model_validate_json(response.text)
        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        ctx.log_step(
            "ResourceAllocator", "solve_constrained_allocation",
            f"Crisis: {cls_out.title} | Available Fleet: {len(inventory.units)} units",
            f"Allocated: {proposal.allocated_units}. Trade-offs: {proposal.trade_off_log[:100]}...",
            duration,
            {"model": settings.GEMINI_MODEL}
        )
        return proposal

    @classmethod
    async def run_impact_simulation(cls, ctx: PipelineContext, cls_out: CrisisClassification, proposal: ResourceAllocationProposal) -> SimulationResult:
        start_time = datetime.utcnow()
        client = cls._get_client()

        prompt = f"""
        Act as the Impact Simulator Agent.
        Evaluate the before/after state, side effects, and draft public/hospital/utility alerts for this crisis and allocation plan:
        Crisis: {cls_out.model_dump_json()}
        Allocation: {proposal.model_dump_json()}

        Rules:
        - If the crisis is a false alarm, output a retraction alert for the public and notice alerts for hospitals and utilities.
        - Produce comprehensive summaries.
        """

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": SimulationResult,
                }
            )
        )

        sim = SimulationResult.model_validate_json(response.text)
        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        ctx.log_step(
            "SimulationAgent", "predict_response_outcomes",
            f"Crisis: {cls_out.title} | Response Action: {proposal.allocated_units}",
            f"Mitigation index: {sim.overall_effectiveness}. Side Effects count: {len(sim.side_effects)}.",
            duration,
            {"model": settings.GEMINI_MODEL}
        )
        return sim


# ──────────────────────────────────────────────
# Main Pipeline Dispatcher
# ──────────────────────────────────────────────

async def run_orchestrator_pipeline(target_signal: IngestedSignal) -> UUID:
    """
    Executes the entire multi-agent pipeline asynchronously.
    Updates the global store (crises, resources, simulations, trace logs).
    """
    ctx = PipelineContext(target_signal)
    pipeline_id = ctx.run_id

    # Create the trace log in store immediately
    await store.add_trace_log(ctx.get_log())

    # Decide if using real API or Fallback
    use_real = bool(settings.GOOGLE_API_KEY and "your-gemini" not in settings.GOOGLE_API_KEY.lower())

    logger.info(f"Starting orchestration pipeline run {pipeline_id} (Gemini API: {use_real})")

    async def _execute(engine: Union[type[GenaiPipeline], type[FallbackPipeline]]) -> None:
        # Step 1: Signal Fusion Node
        all_signals = await store.get_signals(limit=100)
        prepared_signals = _prepare_signals_for_fusion(ctx, all_signals)
        fused = await engine.run_signal_fusion(ctx, prepared_signals)

        # Step 2: Crisis Classifier Agent
        cls_out = await engine.run_crisis_classification(ctx, fused)

        # Update or create crisis state in store
        # First check if we can reuse/update an existing active crisis
        existing_crises = await store.get_crises(active_only=False)
        target_crisis_id = uuid4()
        for c in existing_crises:
            if c.crisis_type == cls_out.crisis_type and c.location.label == cls_out.title.split(" — ")[-1]:
                target_crisis_id = c.id
                break

        # Build crisis model
        crisis_state = CrisisState(
            id=target_crisis_id,
            crisis_type=cls_out.crisis_type,
            title=cls_out.title,
            description=cls_out.description,
            location=fused.fused_location,
            severity=cls_out.severity,
            confidence=cls_out.confidence,
            affected_population=cls_out.affected_population,
            expected_duration_hours=cls_out.expected_duration_hours,
            contributing_signals=fused.signals_analyzed,
            is_false_alarm=cls_out.is_false_alarm,
            false_alarm_reason=cls_out.false_alarm_reason,
            evolutionary_path=[
                EvolutionaryPath(
                    hours_ahead=3,
                    predicted_severity=Severity(max(1, cls_out.severity.value - 1)) if cls_out.is_false_alarm else Severity(min(5, cls_out.severity.value + 1)),
                    trend=EvolutionTrend.DE_ESCALATING if cls_out.is_false_alarm else EvolutionTrend.ESCALATING,
                    narrative="Emergency resolved" if cls_out.is_false_alarm else "Rain / index escalating rapidly",
                )
            ]
        )
        await store.upsert_crisis(crisis_state)

        # Link trace log to crisis
        ctx.get_log(crisis_state.id)

        # Step 3: Resource Allocator Agent
        inventory = await store.get_inventory()
        proposal = await engine.run_resource_allocation(ctx, cls_out, inventory)

        # Step 4: Impact Simulator Agent
        simulation = await engine.run_impact_simulation(ctx, cls_out, proposal)

        # Convert proposal call-signs to resource IDs
        committed_ids = []
        for unit in inventory.units:
            if unit.call_sign in proposal.allocated_units:
                committed_ids.append(unit.id)
                # Update status in inventory
                new_status = ResourceStatus.DEPLOYED if not cls_out.is_false_alarm else ResourceStatus.AVAILABLE
                await store.update_unit_status(unit.id, new_status, None if cls_out.is_false_alarm else crisis_state.id)

        # Save SimulationOutcome
        sim_outcome = SimulationOutcome(
            id=uuid4(),
            crisis_id=crisis_state.id,
            response_action=proposal.trade_off_log,
            resources_committed=committed_ids,
            before_state=simulation.before_state,
            after_state=simulation.after_state,
            side_effects=simulation.side_effects,
            overall_effectiveness=simulation.overall_effectiveness,
            recommendation=f"{simulation.recommendation}\n\n[PUBLIC ALERT] {simulation.public_alert}\n\n[HOSPITAL ALERT] {simulation.hospital_alert}\n\n[UTILITY ALERT] {simulation.utility_alert}"
        )
        await store.add_simulation(sim_outcome)

        # Complete trace entry
        ctx.log_step(
            "OrchestratorAgent", "finalize_pipeline_run",
            "Synthesising final crisis plan.",
            f"Successfully updated inventory and dispatched simulation {sim_outcome.id}. Target crisis {crisis_state.id} update complete.",
            150
        )

        logger.info(f"Pipeline run {pipeline_id} complete. Crisis ID: {crisis_state.id}")

    try:
        if use_real:
            try:
                await _execute(GenaiPipeline)
            except GEMINI_DEGRADED_ERRORS as exc:
                logger.critical(f"CRITICAL: Gemini API error: {type(exc).__name__}: {exc}")
                logger.exception("Full traceback:")
                ctx.log_step(
                    "System",
                    "degraded_mode",
                    "Gemini API error while processing signals.",
                    "Switched to rule-based fallback pipeline.",
                    0,
                    {"error": f"{type(exc).__name__}: {str(exc)}"},
                )
                await _execute(FallbackPipeline)
        else:
            await _execute(FallbackPipeline)

    except Exception as e:
        logger.exception(f"Error in pipeline run {pipeline_id}: {e}")
        ctx.log_step(
            "OrchestratorAgent", "pipeline_error",
            "Handling pipeline exception.",
            f"Exception occurred: {str(e)}",
            100,
            {"error": True}
        )

    return pipeline_id
