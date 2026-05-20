"""
CIRO Data Schemas — Pydantic v2 Models
=======================================
Canonical data contracts for the Crisis Intelligence & Response Orchestrator.
All models use Pydantic v2 with strict validation and JSON-optimised serialisation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────
# Enumerations
# ──────────────────────────────────────────────

class SignalSource(str, Enum):
    """Origin channel for an ingested signal."""
    SOCIAL_MEDIA = "social_media"
    WEATHER_API = "weather_api"
    TRAFFIC_SENSOR = "traffic_sensor"
    NEWS_FEED = "news_feed"
    CITIZEN_REPORT = "citizen_report"
    IOT_DEVICE = "iot_device"


class CrisisType(str, Enum):
    """Broad crisis taxonomy relevant to metropolitan events."""
    URBAN_FLOOD = "urban_flood"
    HEATWAVE = "heatwave"
    EARTHQUAKE = "earthquake"
    FIRE = "fire"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    PUBLIC_HEALTH = "public_health"
    CIVIL_UNREST = "civil_unrest"
    OTHER = "other"


class Severity(str, Enum):
    """1 (minor) → 5 (catastrophic)."""
    MINOR = "1"
    MODERATE = "2"
    SIGNIFICANT = "3"
    SEVERE = "4"
    CATASTROPHIC = "5"


class ResourceType(str, Enum):
    """Emergency resource categories."""
    AMBULANCE = "ambulance"
    POLICE = "police"
    RESCUE_TEAM = "rescue_team"
    FIRE_BRIGADE = "fire_brigade"
    MEDICAL_STAFF = "medical_staff"
    EVACUATION_BUS = "evacuation_bus"


class ResourceStatus(str, Enum):
    """Current deployment state of a resource unit."""
    AVAILABLE = "available"
    DEPLOYED = "deployed"
    EN_ROUTE = "en_route"
    MAINTENANCE = "maintenance"


class EvolutionTrend(str, Enum):
    """Predicted evolutionary direction of a crisis."""
    ESCALATING = "escalating"
    STABLE = "stable"
    DE_ESCALATING = "de_escalating"
    RESOLVED = "resolved"


# ──────────────────────────────────────────────
# 1. Ingested Signals
# ──────────────────────────────────────────────

class GeoLocation(BaseModel):
    """Latitude / longitude pair with optional label."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    label: Optional[str] = Field(None, max_length=256)


class WeatherMetrics(BaseModel):
    """Structured weather readings attached to a signal."""
    temperature_c: Optional[float] = Field(None, description="Temperature in °C")
    humidity_pct: Optional[float] = Field(None, ge=0, le=100, description="Relative humidity %")
    rainfall_mm: Optional[float] = Field(None, ge=0, description="Rainfall in mm (last hour)")
    wind_speed_kmh: Optional[float] = Field(None, ge=0, description="Wind speed km/h")
    heat_index_c: Optional[float] = Field(None, description="Apparent temperature / heat index °C")


class TrafficData(BaseModel):
    """Traffic congestion metrics from sensors or map APIs."""
    congestion_level: float = Field(..., ge=0, le=1, description="0 = free flow, 1 = gridlock")
    avg_speed_kmh: Optional[float] = Field(None, ge=0)
    incident_count: int = Field(0, ge=0, description="Active incidents on the route/zone")
    road_closures: int = Field(0, ge=0)


class IngestedSignal(BaseModel):
    """
    A raw signal ingested from any source.

    This is the fundamental unit entering the CIRO pipeline.  Each signal
    carries its provenance, optional structured payloads (weather, traffic),
    and a reliability estimate so downstream agents can weight evidence.
    """
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: SignalSource
    raw_text: Optional[str] = Field(None, max_length=4096, description="Free-text content (social post, news snippet, citizen report)")
    location: Optional[GeoLocation] = None
    weather: Optional[WeatherMetrics] = None
    traffic: Optional[TrafficData] = None
    media_urls: list[str] = Field(default_factory=list, description="URLs to attached images/videos")
    reliability_score: float = Field(0.5, ge=0, le=1, description="Source reliability estimate (0 = untrusted, 1 = verified)")

    model_config = {"json_schema_extra": {"examples": [
        {
            "source": "social_media",
            "raw_text": "Water level rising fast in G-10 sector, cars submerged near main market #IslamabadFloods",
            "location": {"latitude": 33.6844, "longitude": 73.0479, "label": "G-10/4, Islamabad"},
            "reliability_score": 0.4,
        }
    ]}}


# ──────────────────────────────────────────────
# 2. Crisis State
# ──────────────────────────────────────────────

class EvolutionaryPath(BaseModel):
    """Predicted future trajectory of a crisis at a given look-ahead."""
    hours_ahead: int = Field(..., ge=1, le=72)
    predicted_severity: Severity
    trend: EvolutionTrend
    narrative: str = Field(..., max_length=1024, description="Human-readable projection summary")


class CrisisState(BaseModel):
    """
    Canonical snapshot of a classified crisis event.

    Produced by the Signal Fusion → Classification stage of the agentic
    pipeline.  Downstream agents (Resource Optimiser, Simulator) consume
    this as their primary input.
    """
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    crisis_type: CrisisType
    title: str = Field(..., max_length=256, examples=["Urban Flooding — G-10 Islamabad"])
    description: str = Field("", max_length=2048)

    location: GeoLocation
    severity: Severity
    confidence: float = Field(..., ge=0, le=1, description="Model confidence in classification")

    affected_population: int = Field(0, ge=0, description="Estimated individuals impacted")
    expected_duration_hours: float = Field(0, ge=0, description="Forecast duration in hours")

    contributing_signals: list[UUID] = Field(default_factory=list, description="IDs of IngestedSignals that formed this state")
    evolutionary_path: list[EvolutionaryPath] = Field(default_factory=list, description="Time-stepped severity projections")
    is_false_alarm: bool = Field(False, description="Flag set by false-alarm detection agent")
    false_alarm_reason: Optional[str] = Field(None, max_length=1024)

    @field_validator("confidence")
    @classmethod
    def _round_confidence(cls, v: float) -> float:
        return round(v, 4)


# ──────────────────────────────────────────────
# 3. Resource Inventory
# ──────────────────────────────────────────────

class ResourceUnit(BaseModel):
    """A single deployable emergency resource unit."""
    id: UUID = Field(default_factory=uuid4)
    resource_type: ResourceType
    call_sign: str = Field(..., max_length=64, examples=["AMB-ISB-042"])
    status: ResourceStatus = ResourceStatus.AVAILABLE
    current_location: Optional[GeoLocation] = None
    assigned_crisis_id: Optional[UUID] = Field(None, description="Crisis this unit is responding to")
    capacity: int = Field(1, ge=1, description="Personnel / patient slots")


class ResourceInventory(BaseModel):
    """
    Aggregated view of all emergency assets in a jurisdiction.

    The Resource Optimiser agent uses this to solve constrained-allocation
    problems and propose deployment plans.
    """
    snapshot_time: datetime = Field(default_factory=datetime.utcnow)
    jurisdiction: str = Field("Islamabad Capital Territory", max_length=128)
    units: list[ResourceUnit] = Field(default_factory=list)

    @property
    def available(self) -> list[ResourceUnit]:
        return [u for u in self.units if u.status == ResourceStatus.AVAILABLE]

    @property
    def deployed(self) -> list[ResourceUnit]:
        return [u for u in self.units if u.status == ResourceStatus.DEPLOYED]

    @property
    def summary(self) -> dict[str, dict[str, int]]:
        """Returns {resource_type: {available: n, deployed: n, total: n}}."""
        out: dict[str, dict[str, int]] = {}
        for u in self.units:
            key = u.resource_type.value
            bucket = out.setdefault(key, {"available": 0, "deployed": 0, "total": 0})
            bucket["total"] += 1
            if u.status == ResourceStatus.AVAILABLE:
                bucket["available"] += 1
            elif u.status == ResourceStatus.DEPLOYED:
                bucket["deployed"] += 1
        return out


# ──────────────────────────────────────────────
# 4. Simulation Outcome
# ──────────────────────────────────────────────

class StateSnapshot(BaseModel):
    """Point-in-time capture of crisis metrics for before/after comparison."""
    severity: Severity
    affected_population: int = Field(0, ge=0)
    infrastructure_damage_pct: float = Field(0, ge=0, le=100)
    casualties_estimate: int = Field(0, ge=0)
    economic_impact_usd: float = Field(0, ge=0)
    narrative: str = Field("", max_length=1024)


class SideEffect(BaseModel):
    """An unintended consequence identified by the simulation agent."""
    description: str = Field(..., max_length=512)
    probability: float = Field(..., ge=0, le=1)
    impact_severity: Severity


class SimulationOutcome(BaseModel):
    """
    Result of a what-if simulation run by the Simulation Agent.

    Compares the projected before-state (no intervention) against the
    expected after-state (with the proposed response action), including
    any identified side effects.
    """
    id: UUID = Field(default_factory=uuid4)
    crisis_id: UUID = Field(..., description="The CrisisState this simulation targets")
    run_at: datetime = Field(default_factory=datetime.utcnow)

    response_action: str = Field(..., max_length=1024, description="Plain-language description of the proposed intervention")
    resources_committed: list[UUID] = Field(default_factory=list, description="ResourceUnit IDs allocated in this scenario")

    before_state: StateSnapshot = Field(..., description="Projected outcome with NO intervention")
    after_state: StateSnapshot = Field(..., description="Projected outcome WITH the proposed intervention")
    side_effects: list[SideEffect] = Field(default_factory=list)

    overall_effectiveness: float = Field(..., ge=0, le=1, description="Composite score: 1 = perfect mitigation")
    recommendation: str = Field("", max_length=1024, description="Agentic recommendation summary")


# ──────────────────────────────────────────────
# 5. Trace Log (Agentic Transparency)
# ──────────────────────────────────────────────

class TraceEntry(BaseModel):
    """
    A single step in the agentic reasoning chain.

    Collected into a TraceLog so the dashboard can surface full
    transparency into how decisions were made.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_name: str = Field(..., max_length=128)
    action: str = Field(..., max_length=256)
    input_summary: str = Field("", max_length=1024)
    output_summary: str = Field("", max_length=1024)
    duration_ms: int = Field(0, ge=0)
    metadata: dict = Field(default_factory=dict)


class TraceLog(BaseModel):
    """Full trace of a pipeline execution for audit & dashboard display."""
    pipeline_run_id: UUID = Field(default_factory=uuid4)
    crisis_id: Optional[UUID] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    entries: list[TraceEntry] = Field(default_factory=list)
