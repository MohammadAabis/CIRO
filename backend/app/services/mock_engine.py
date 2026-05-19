"""
CIRO Mock Data Engine
======================
Stress-test scenario generator for the Anti Gravity Hackathon.

Simulates three interleaved scenarios:
  1. Heavy rain + social media flooding chatter in G-10 + traffic spike
  2. Conflicting field report: broken water main (not a flash flood)
  3. Simultaneous heatwave emergency in F-8 competing for resources

Also seeds a realistic resource inventory and simulation outcomes.
Can be run standalone (`python -m app.services.mock_engine`) or
auto-loaded at server startup via the lifespan hook.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.schemas import (
    CrisisState, CrisisType, EvolutionaryPath, EvolutionTrend,
    GeoLocation, IngestedSignal, ResourceInventory, ResourceStatus,
    ResourceType, ResourceUnit, Severity, SideEffect,
    SimulationOutcome, SignalSource, StateSnapshot,
    TraceEntry, TraceLog, TrafficData, WeatherMetrics,
)
from app.store import store

NOW = datetime.utcnow()


# ═══════════════════════════════════════════════
# 1. RESOURCE INVENTORY (Islamabad fleet)
# ═══════════════════════════════════════════════

def _build_inventory() -> ResourceInventory:
    units: list[ResourceUnit] = []
    fleet = [
        (ResourceType.AMBULANCE,    "AMB", 6, 2),
        (ResourceType.POLICE,       "POL", 8, 4),
        (ResourceType.RESCUE_TEAM,  "RSC", 4, 2),
        (ResourceType.FIRE_BRIGADE, "FBR", 3, 1),
        (ResourceType.MEDICAL_STAFF,"MED", 5, 3),
        (ResourceType.EVACUATION_BUS,"EVB", 3, 1),
    ]
    for rtype, prefix, total, capacity in fleet:
        for i in range(1, total + 1):
            units.append(ResourceUnit(
                resource_type=rtype,
                call_sign=f"{prefix}-ISB-{i:03d}",
                status=ResourceStatus.AVAILABLE,
                current_location=GeoLocation(
                    latitude=33.68 + random.uniform(-0.05, 0.05),
                    longitude=73.04 + random.uniform(-0.05, 0.05),
                    label="Islamabad HQ",
                ),
                capacity=capacity,
            ))
    return ResourceInventory(
        jurisdiction="Islamabad Capital Territory",
        units=units,
    )


def build_default_inventory() -> ResourceInventory:
    """Expose the default mock inventory for live-ingestion mode."""
    return _build_inventory()


# ═══════════════════════════════════════════════
# 2. SCENARIO SIGNALS
# ═══════════════════════════════════════════════

G10 = GeoLocation(latitude=33.6844, longitude=73.0479, label="G-10/4, Islamabad")
G10_MKT = GeoLocation(latitude=33.6831, longitude=73.0502, label="G-10 Markaz")
F8 = GeoLocation(latitude=33.7060, longitude=73.0551, label="F-8/3, Islamabad")

def _scenario_signals() -> list[IngestedSignal]:
    """Generate the three-scenario signal timeline."""
    sigs: list[IngestedSignal] = []

    # ── Scenario 1: Flood signals ──────────────
    sigs.append(IngestedSignal(
        timestamp=NOW - timedelta(minutes=45),
        source=SignalSource.WEATHER_API,
        raw_text="ALERT: Heavy rainfall expected 80-120mm in next 3h over Islamabad sectors G-9 to G-11",
        location=G10,
        weather=WeatherMetrics(
            temperature_c=24.0, humidity_pct=94.0,
            rainfall_mm=82.0, wind_speed_kmh=35.0,
        ),
        reliability_score=0.95,
    ))
    sigs.append(IngestedSignal(
        timestamp=NOW - timedelta(minutes=38),
        source=SignalSource.SOCIAL_MEDIA,
        raw_text="Water level rising fast in G-10 sector, cars submerged near main market #IslamabadFloods #G10",
        location=G10_MKT,
        reliability_score=0.4,
    ))
    sigs.append(IngestedSignal(
        timestamp=NOW - timedelta(minutes=35),
        source=SignalSource.SOCIAL_MEDIA,
        raw_text="My basement is completely flooded in G-10/4. Need help ASAP! @NDMA @DCIslamabad",
        location=G10,
        reliability_score=0.45,
    ))
    sigs.append(IngestedSignal(
        timestamp=NOW - timedelta(minutes=30),
        source=SignalSource.TRAFFIC_SENSOR,
        raw_text="Massive congestion spike detected on Khayaban-e-Suharwardy near G-10",
        location=G10,
        traffic=TrafficData(
            congestion_level=0.89, avg_speed_kmh=8.0,
            incident_count=3, road_closures=2,
        ),
        reliability_score=0.92,
    ))
    sigs.append(IngestedSignal(
        timestamp=NOW - timedelta(minutes=28),
        source=SignalSource.SOCIAL_MEDIA,
        raw_text="Families trapped on rooftops in G-10/2. Rescue teams please hurry! #FloodRelief",
        location=GeoLocation(latitude=33.6855, longitude=73.0465, label="G-10/2"),
        reliability_score=0.5,
    ))
    sigs.append(IngestedSignal(
        timestamp=NOW - timedelta(minutes=25),
        source=SignalSource.NEWS_FEED,
        raw_text="BREAKING: Flash flood warning issued for G-10 and adjacent sectors. CDA activates emergency drains.",
        location=G10,
        reliability_score=0.88,
    ))

    # ── Scenario 2: Conflicting field report ───
    sigs.append(IngestedSignal(
        timestamp=NOW - timedelta(minutes=20),
        source=SignalSource.CITIZEN_REPORT,
        raw_text="FIELD REPORT: Water main burst on 7th Avenue near G-10. Not flash flooding — broken infrastructure pipe. Water gushing from underground.",
        location=GeoLocation(latitude=33.6840, longitude=73.0490, label="7th Ave / G-10 junction"),
        reliability_score=0.72,
    ))
    sigs.append(IngestedSignal(
        timestamp=NOW - timedelta(minutes=18),
        source=SignalSource.IOT_DEVICE,
        raw_text="Water pressure drop detected: Sector G-10 main supply line. Pressure: 12 PSI (normal: 55 PSI).",
        location=G10,
        reliability_score=0.90,
    ))

    # ── Scenario 3: Simultaneous heatwave in F-8 ─
    sigs.append(IngestedSignal(
        timestamp=NOW - timedelta(minutes=15),
        source=SignalSource.WEATHER_API,
        raw_text="EXTREME HEAT: Temperature 47°C in F-8. Heat index 52°C. Multiple heat stroke cases reported at F-8 Markaz.",
        location=F8,
        weather=WeatherMetrics(
            temperature_c=47.0, humidity_pct=28.0,
            rainfall_mm=0.0, wind_speed_kmh=5.0,
            heat_index_c=52.0,
        ),
        reliability_score=0.93,
    ))
    sigs.append(IngestedSignal(
        timestamp=NOW - timedelta(minutes=12),
        source=SignalSource.CITIZEN_REPORT,
        raw_text="3 elderly people collapsed at F-8 park due to heat. One is unconscious. Ambulance needed urgently!",
        location=F8,
        reliability_score=0.65,
    ))
    sigs.append(IngestedSignal(
        timestamp=NOW - timedelta(minutes=8),
        source=SignalSource.NEWS_FEED,
        raw_text="Hospitals in F-8 and G-9 overwhelmed with heat stroke patients. PIMS declares emergency capacity.",
        location=GeoLocation(latitude=33.6950, longitude=73.0480, label="PIMS Hospital"),
        reliability_score=0.85,
    ))

    return sigs


# ═══════════════════════════════════════════════
# 3. CRISIS STATES (derived from signals)
# ═══════════════════════════════════════════════

def _build_crises(signal_ids: list) -> list[CrisisState]:
    flood_id = uuid4()
    heat_id = uuid4()
    false_alarm_id = uuid4()

    flood = CrisisState(
        id=flood_id,
        crisis_type=CrisisType.URBAN_FLOOD,
        title="Urban Flooding — G-10 Islamabad",
        description="Multiple corroborated reports of severe flooding in G-10 sector. Basements submerged, families trapped, traffic gridlocked. Heavy rainfall ongoing.",
        location=G10,
        severity=Severity.SEVERE,
        confidence=0.87,
        affected_population=12000,
        expected_duration_hours=8.0,
        contributing_signals=signal_ids[:6],
        evolutionary_path=[
            EvolutionaryPath(hours_ahead=2, predicted_severity=Severity.CATASTROPHIC,
                             trend=EvolutionTrend.ESCALATING,
                             narrative="Rain continues; water levels projected +40cm in 2h"),
            EvolutionaryPath(hours_ahead=6, predicted_severity=Severity.SEVERE,
                             trend=EvolutionTrend.STABLE,
                             narrative="Rain tapering off but drainage overwhelmed"),
            EvolutionaryPath(hours_ahead=12, predicted_severity=Severity.MODERATE,
                             trend=EvolutionTrend.DE_ESCALATING,
                             narrative="Water receding as pumps engage; cleanup phase begins"),
        ],
    )

    false_alarm = CrisisState(
        id=false_alarm_id,
        crisis_type=CrisisType.INFRASTRUCTURE_FAILURE,
        title="Broken Water Main — 7th Ave / G-10 (RECLASSIFIED)",
        description="Initial reports suggested flash flooding. Field investigation and IoT pressure data confirm a burst water main on 7th Avenue. CDA repair crew dispatched.",
        location=GeoLocation(latitude=33.6840, longitude=73.0490, label="7th Ave / G-10"),
        severity=Severity.MODERATE,
        confidence=0.78,
        affected_population=2000,
        expected_duration_hours=4.0,
        contributing_signals=signal_ids[6:8],
        is_false_alarm=True,
        false_alarm_reason="Signal fusion reclassified: flooding in this zone caused by burst water main, not weather. IoT pressure data confirms infrastructure failure.",
    )

    heatwave = CrisisState(
        id=heat_id,
        crisis_type=CrisisType.HEATWAVE,
        title="Extreme Heatwave — F-8 Islamabad",
        description="Temperature 47°C with heat index 52°C. Multiple heat stroke casualties. Hospitals nearing capacity. Competing for medical resources with G-10 flood response.",
        location=F8,
        severity=Severity.SIGNIFICANT,
        confidence=0.91,
        affected_population=25000,
        expected_duration_hours=14.0,
        contributing_signals=signal_ids[8:11],
        evolutionary_path=[
            EvolutionaryPath(hours_ahead=3, predicted_severity=Severity.SEVERE,
                             trend=EvolutionTrend.ESCALATING,
                             narrative="Peak afternoon heat; casualties expected to rise"),
            EvolutionaryPath(hours_ahead=8, predicted_severity=Severity.SIGNIFICANT,
                             trend=EvolutionTrend.STABLE,
                             narrative="Evening brings slight relief but urban heat island persists"),
            EvolutionaryPath(hours_ahead=18, predicted_severity=Severity.MODERATE,
                             trend=EvolutionTrend.DE_ESCALATING,
                             narrative="Nighttime cooling; remaining cases stabilise"),
        ],
    )

    return [flood, false_alarm, heatwave]


# ═══════════════════════════════════════════════
# 4. SIMULATION OUTCOMES
# ═══════════════════════════════════════════════

def _build_simulations(crises: list[CrisisState], unit_ids: list) -> list[SimulationOutcome]:
    flood = crises[0]
    heat = crises[2]

    sim_flood = SimulationOutcome(
        crisis_id=flood.id,
        response_action="Deploy 4 rescue teams + 3 ambulances to G-10. Evacuate low-lying blocks via 2 buses. Activate emergency pumps at G-10 drains.",
        resources_committed=unit_ids[:9],
        before_state=StateSnapshot(
            severity=Severity.CATASTROPHIC,
            affected_population=15000,
            infrastructure_damage_pct=35.0,
            casualties_estimate=12,
            economic_impact_usd=2_500_000,
            narrative="Without intervention: water rises 60cm more, 15k affected, structural damage to 200+ homes.",
        ),
        after_state=StateSnapshot(
            severity=Severity.SIGNIFICANT,
            affected_population=8000,
            infrastructure_damage_pct=18.0,
            casualties_estimate=2,
            economic_impact_usd=900_000,
            narrative="With intervention: evacuations save ~7k people, pumps reduce water 40%, casualties minimised.",
        ),
        side_effects=[
            SideEffect(description="Traffic gridlock worsens on Margalla Rd due to rerouted emergency vehicles", probability=0.7, impact_severity=Severity.MINOR),
            SideEffect(description="Resource diversion weakens heatwave response in F-8 by 30%", probability=0.85, impact_severity=Severity.MODERATE),
        ],
        overall_effectiveness=0.73,
        recommendation="DEPLOY IMMEDIATELY. Accept minor traffic disruption. Coordinate with F-8 heatwave team to share medical staff on rotating shifts.",
    )

    sim_heat = SimulationOutcome(
        crisis_id=heat.id,
        response_action="Deploy 3 ambulances + 2 medical teams to F-8. Set up 4 cooling stations at F-8 Markaz, park, and mosques. Issue city-wide heat advisory via SMS.",
        resources_committed=unit_ids[9:14],
        before_state=StateSnapshot(
            severity=Severity.SEVERE,
            affected_population=30000,
            infrastructure_damage_pct=5.0,
            casualties_estimate=8,
            economic_impact_usd=500_000,
            narrative="Without intervention: 8+ heat stroke fatalities, overwhelmed ERs, potential grid failure.",
        ),
        after_state=StateSnapshot(
            severity=Severity.MODERATE,
            affected_population=18000,
            infrastructure_damage_pct=3.0,
            casualties_estimate=1,
            economic_impact_usd=200_000,
            narrative="Cooling stations reduce exposure. SMS alerts keep 12k indoors. Medical teams treat 45 patients on-site.",
        ),
        side_effects=[
            SideEffect(description="Power grid strain from cooling station generators", probability=0.4, impact_severity=Severity.MINOR),
        ],
        overall_effectiveness=0.81,
        recommendation="DEPLOY. Cooling stations are high-impact, low-cost. Coordinate with IESCO for backup power.",
    )

    return [sim_flood, sim_heat]


# ═══════════════════════════════════════════════
# 5. TRACE LOGS (simulated agent reasoning)
# ═══════════════════════════════════════════════

def _build_trace(crisis_id) -> TraceLog:
    log = TraceLog(crisis_id=crisis_id, started_at=NOW - timedelta(minutes=44))
    entries = [
        ("SignalFusionAgent", "ingest_signals", "Received 6 raw signals from weather, social media, traffic", "Correlated 6 signals → cluster centroid at G-10/4 (radius 0.8km)", 320),
        ("SignalFusionAgent", "deduplicate", "Checking 4 social media posts for semantic overlap", "Merged 2 near-duplicate posts. 5 unique signals remain.", 180),
        ("CrisisClassifier", "classify_event", "Input: 5 fused signals with weather + traffic data", "Classification: URBAN_FLOOD (confidence 0.87). Severity: 4/5.", 450),
        ("CrisisClassifier", "false_alarm_check", "Cross-referencing IoT pressure data with flood hypothesis", "ALERT: Conflicting evidence — water main burst detected. Splitting into 2 events.", 280),
        ("ResourceOptimiser", "assess_inventory", "29 units across 6 types. 2 concurrent crises detected.", "Available: 29/29. Constraint: shared medical pool between flood + heatwave.", 150),
        ("ResourceOptimiser", "solve_allocation", "Optimising for minimum casualties across both crises", "Allocation plan: 9 units → flood, 5 units → heatwave. Rotating medical shifts.", 890),
        ("SimulationAgent", "run_what_if", "Before/after modelling for flood response plan", "Effectiveness 0.73. Side effect: 30% weaker heatwave response.", 1200),
        ("SimulationAgent", "run_what_if", "Before/after modelling for heatwave response plan", "Effectiveness 0.81. Cooling stations are primary lever.", 980),
        ("OrchestratorAgent", "synthesise_plan", "Merging flood + heatwave response plans", "FINAL PLAN: Deploy in 2 waves. Wave 1: flood rescue. Wave 2 (+15min): heatwave cooling.", 340),
    ]
    for i, (agent, action, inp, out, ms) in enumerate(entries):
        log.entries.append(TraceEntry(
            timestamp=NOW - timedelta(minutes=44 - i * 3),
            agent_name=agent,
            action=action,
            input_summary=inp,
            output_summary=out,
            duration_ms=ms,
        ))
    return log


# ═══════════════════════════════════════════════
# SEED FUNCTION (called from lifespan)
# ═══════════════════════════════════════════════

async def seed_hackathon_scenario() -> None:
    """Populate the in-memory store with the full hackathon scenario."""
    # 1. Resources
    inventory = _build_inventory()
    await store.set_inventory(inventory)
    unit_ids = [u.id for u in inventory.units]

    # 2. Signals
    signals = _scenario_signals()
    for sig in signals:
        await store.add_signal(sig)
    signal_ids = [s.id for s in signals]

    # 3. Crises
    crises = _build_crises(signal_ids)
    for crisis in crises:
        await store.upsert_crisis(crisis)

    # 4. Simulations
    sims = _build_simulations(crises, unit_ids)
    for sim in sims:
        await store.add_simulation(sim)

    # 5. Trace log
    trace = _build_trace(crises[0].id)
    await store.add_trace_log(trace)

    print(f"[CIRO] Mock data seeded: {len(signals)} signals, "
          f"{len(crises)} crises, {len(sims)} simulations, "
          f"{len(inventory.units)} resource units, 1 trace log")


# ── Standalone runner ───────────────────────────
if __name__ == "__main__":
    asyncio.run(seed_hackathon_scenario())
    print("[CIRO] Standalone seed complete.")
