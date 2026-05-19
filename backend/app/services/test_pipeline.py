import asyncio
import httpx
import json

async def run_test():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # 1. Verify health
        r = await client.get("/health")
        print("Health check status:", r.status_code)

        # 2. Check stats before
        stats_before = (await client.get("/api/v1/crises/stats")).json()
        print(f"Stats Before: Active Crises: {stats_before['active_crises']}, False Alarms: {stats_before['false_alarms']}")

        # 3. Ingest the recovery scenario correction signal
        payload = {
            "source": "citizen_report",
            "raw_text": "FIELD UPDATE: 7th Avenue water main burst confirmed. Telemetry pressure drops. Retract previous flash flood alerts. This is a local pipe burst.",
            "location": {
                "latitude": 33.6840,
                "longitude": 73.0490,
                "label": "7th Ave / G-10 junction"
            },
            "reliability_score": 0.95
        }
        print("Ingesting field correction signal...")
        r = await client.post("/api/v1/ingest", json=payload)
        print("Ingest status:", r.status_code, r.json())

        # 4. Wait for background agents to run
        print("Waiting 3 seconds for agentic orchestration pipeline to execute...")
        await asyncio.sleep(3.0)

        # 5. Check stats after
        stats_after = (await client.get("/api/v1/crises/stats")).json()
        print(f"Stats After: Active Crises: {stats_after['active_crises']}, False Alarms: {stats_after['false_alarms']}")

        # 6. Fetch trace logs to verify transparent reasoning
        traces = (await client.get("/api/v1/traces/")).json()
        print(f"Total Trace Logs: {traces['count']}")
        if traces['count'] > 0:
            latest_run = traces['traces'][0]
            print(f"Latest Agent Run ID: {latest_run['pipeline_run_id']}")
            print("Reasoning Chain:")
            for entry in latest_run['entries']:
                print(f"  [{entry['agent_name']} -> {entry['action']}]")
                print(f"    In:  {entry['input_summary'][:120]}")
                print(f"    Out: {entry['output_summary'][:120]}")

        # 7. Fetch simulations to verify retracted alerts
        sims = (await client.get("/api/v1/simulations/")).json()
        print(f"Total Simulation outcomes: {sims['count']}")
        for sim in sims['simulations'][:1]:
            print("Latest Simulation Mitigation Action:")
            print("  Response action:", sim['response_action'])
            print("  Recommendation details:", sim['recommendation'][:300] + "...")

if __name__ == "__main__":
    asyncio.run(run_test())
