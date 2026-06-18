from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse

from api.deps import get_storage
from api.errors import api_error
from api.storage import InMemoryArchimedesStorage


router = APIRouter(prefix="/sessions/{session_id}/events", tags=["events"])


def _value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return str(value)


def build_session_events(storage: InMemoryArchimedesStorage, session_id: str) -> list[dict[str, Any]]:
    session = storage.read_session(session_id)
    if session is None:
        raise api_error(404, f"Session not found: {session_id}", "session_not_found")

    events: list[dict[str, Any]] = []
    for stage, execution in session.stage_executions.items():
        stage_value = _value(stage)
        timestamp = execution.completed_at or execution.started_at or session.updated_at
        events.append(
            {
                "event_id": f"evt_{stage_value}_{_value(execution.status)}",
                "event_type": f"stage_{_value(execution.status)}",
                "session_id": session_id,
                "stage": stage_value,
                "stage_run_id": execution.stage_run_id,
                "message": f"{stage_value.replace('_', ' ').title()} is {_value(execution.status)}.",
                "percent": 100 if _value(execution.status) == "completed" else 0,
                "timestamp": _iso(timestamp),
            }
        )

    for event in storage.list_change_events(session_id):
        events.append(
            {
                "event_id": f"evt_{event.change_event_id}",
                "event_type": "requirement_change_submitted",
                "session_id": session_id,
                "stage": "rereasoning",
                "stage_run_id": None,
                "message": event.user_message or event.new_value_summary or event.changed_field,
                "percent": 100,
                "timestamp": _iso(event.timestamp),
                "payload": {
                    "change_event_id": event.change_event_id,
                    "impacted_stages": [_value(stage) for stage in event.impacted_stages],
                    "stable_stages": [_value(stage) for stage in event.stable_stages],
                },
            }
        )

    return sorted(events, key=lambda item: item["timestamp"])


@router.get("")
async def list_session_events(
    session_id: str,
    after_event_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> dict[str, Any]:
    events = build_session_events(storage, session_id)
    if after_event_id:
        ids = [event["event_id"] for event in events]
        if after_event_id in ids:
            events = events[ids.index(after_event_id) + 1 :]
    return {"items": events[-limit:], "total": len(events[-limit:])}


@router.get("/stream")
async def stream_session_events(
    session_id: str,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> StreamingResponse:
    events = build_session_events(storage, session_id)
    if last_event_id:
        ids = [event["event_id"] for event in events]
        if last_event_id in ids:
            events = events[ids.index(last_event_id) + 1 :]

    async def event_stream():
        for event in events:
            yield f"id: {event['event_id']}\nevent: {event['event_type']}\ndata: {json.dumps(event, default=str)}\n\n"
        yield ": heartbeat\n\n"
        await asyncio.sleep(0)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
