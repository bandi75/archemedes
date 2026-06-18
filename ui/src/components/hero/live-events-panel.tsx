"use client";

import { useEffect, useState } from "react";
import { RadioTower } from "lucide-react";
import { StatusBadge } from "@/components/shared/status-badge";
import type { SessionEvent } from "@/lib/view-models";

type LiveEventsPanelProps = {
  sessionId: string;
  initialEvents: SessionEvent[];
};

const API_URL = process.env.NEXT_PUBLIC_ARCHIMEDES_API_URL ?? "http://localhost:8000/api/v1";

export function LiveEventsPanel({ sessionId, initialEvents }: LiveEventsPanelProps) {
  const [events, setEvents] = useState(initialEvents);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (process.env.NEXT_PUBLIC_ARCHIMEDES_MOCK_DATA !== "false") {
      return;
    }
    const source = new EventSource(`${API_URL}/sessions/${sessionId}/events/stream`);
    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);
    source.onmessage = (message) => {
      const event = JSON.parse(message.data) as SessionEvent;
      setEvents((current) => {
        if (current.some((item) => item.event_id === event.event_id)) {
          return current;
        }
        return [...current, event].slice(-20);
      });
    };
    return () => source.close();
  }, [sessionId]);

  return (
    <section className="rounded-lg border border-border bg-panel shadow-panel">
      <div className="flex items-center justify-between border-b border-border px-5 py-4">
        <div className="flex items-center gap-2">
          <RadioTower className="h-4 w-4 text-accent" aria-hidden="true" />
          <h2 className="text-base font-semibold text-ink">Live reasoning trace</h2>
        </div>
        <StatusBadge variant={connected ? "success" : "info"}>{connected ? "Streaming" : "Snapshot"}</StatusBadge>
      </div>
      <ol className="space-y-3 p-5">
        {events.map((event) => (
          <li key={event.event_id} className="rounded-md border border-border bg-surface p-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium text-ink">{event.message}</p>
              <span className="shrink-0 text-xs text-ink-subtle">{event.percent ?? 0}%</span>
            </div>
            <p className="mt-1 text-xs text-ink-muted">
              {formatEventTime(event.timestamp)} | {event.stage ?? "session"} | {event.event_type}
            </p>
          </li>
        ))}
      </ol>
    </section>
  );
}

function formatEventTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}
