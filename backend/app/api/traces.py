"""Traces API — SSE streaming of live agent reasoning traces."""

import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.store import store

router = APIRouter()


@router.get("/", summary="List all trace logs")
async def list_traces():
    logs = await store.get_trace_logs()
    return {
        "count": len(logs),
        "traces": [t.model_dump(mode="json") for t in logs],
    }


@router.get("/stream", summary="SSE stream of live agent trace entries")
async def stream_traces(request: Request):
    """
    Server-Sent Events endpoint.
    Clients connect and receive real-time trace entries as agents execute.
    Each event is a JSON-serialised TraceEntry.
    """
    queue = store.subscribe_traces()

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    entry = await asyncio.wait_for(queue.get(), timeout=30.0)
                    data = json.dumps(entry.model_dump(mode="json"), default=str)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive comment to prevent proxy timeouts
                    yield ": keepalive\n\n"
        finally:
            store.unsubscribe_traces(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
