"use client";

import { useState } from "react";
import { Check, GitBranch, Pause, Play, Plus, RotateCcw, Square, StepForward } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_ARCHIMEDES_API_URL ?? "http://localhost:8000/api/v1";

type ActionState = {
  sessionId?: string;
  changeEventId?: string;
  currentStage?: string;
  stageRunId?: string;
  message: string;
};

export function SessionActions() {
  const [state, setState] = useState<ActionState>({ message: "Ready" });

  async function createSession() {
    try {
      const response = await fetch(`${API_URL}/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: "React hero demo",
          business_need: "Design a real-time fraud detection platform on Azure for 10K TPS with PCI-DSS constraints.",
        }),
      });
      const payload = await response.json();
      setState({ sessionId: payload.session_id, currentStage: payload.current_stage, message: "Session created" });
    } catch {
      setState({ message: "API unavailable; mock UI remains active" });
    }
  }

  async function runStage() {
    if (!state.sessionId) {
      setState((current) => ({ ...current, message: "Create a session first" }));
      return;
    }
    try {
      const response = await fetch(`${API_URL}/sessions/${state.sessionId}/pipeline/run-next`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "standard" }),
      });
      const payload = await response.json();
      setState((current) => ({
        ...current,
        currentStage: payload.stage,
        stageRunId: payload.stage_run_id,
        message: "Stage run requested",
      }));
    } catch {
      setState((current) => ({ ...current, message: "Stage request failed locally" }));
    }
  }

  async function submitChange() {
    if (!state.sessionId) {
      setState((current) => ({ ...current, message: "Create a session first" }));
      return;
    }
    try {
      const response = await fetch(`${API_URL}/sessions/${state.sessionId}/changes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          changed_field: "scale",
          old_value_summary: "10K TPS",
          new_value_summary: "100K TPS and active-active regions",
          user_message: "Actually make it 100K TPS and multi-region active-active",
        }),
      });
      const payload = await response.json();
      setState((current) => ({
        ...current,
        changeEventId: payload.change_event_id,
        message: "Change impact ready",
      }));
    } catch {
      setState((current) => ({ ...current, message: "Change request failed locally" }));
    }
  }

  async function pausePipeline() {
    if (!state.sessionId) {
      setState((current) => ({ ...current, message: "Create a session first" }));
      return;
    }
    await fetch(`${API_URL}/sessions/${state.sessionId}/pipeline/pause`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason: "User requested pause from React hero controls" }),
    });
    setState((current) => ({ ...current, message: "Pipeline paused" }));
  }

  async function resumePipeline() {
    if (!state.sessionId) {
      setState((current) => ({ ...current, message: "Create a session first" }));
      return;
    }
    await fetch(`${API_URL}/sessions/${state.sessionId}/pipeline/resume`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_from: "last_successful_stage" }),
    });
    setState((current) => ({ ...current, message: "Pipeline resumed" }));
  }

  async function retryStage() {
    if (!state.sessionId || !state.currentStage) {
      setState((current) => ({ ...current, message: "Run a stage first" }));
      return;
    }
    const response = await fetch(`${API_URL}/sessions/${state.sessionId}/pipeline/stages/${state.currentStage}/retry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason: "Retry from React hero controls" }),
    });
    const payload = await response.json();
    setState((current) => ({
      ...current,
      stageRunId: payload.stage_run_id,
      message: "Stage retry requested",
    }));
  }

  async function cancelStageRun() {
    if (!state.sessionId || !state.stageRunId) {
      setState((current) => ({ ...current, message: "Run or retry a stage first" }));
      return;
    }
    await fetch(`${API_URL}/sessions/${state.sessionId}/pipeline/stage-runs/${state.stageRunId}/cancel`, {
      method: "POST",
    });
    setState((current) => ({ ...current, message: "Cancel requested" }));
  }

  return (
    <div className="rounded-lg border border-border bg-panel p-4 shadow-panel">
      <div className="flex flex-wrap gap-2">
        <button className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-surface px-3 text-sm font-medium text-ink" onClick={runStage} type="button">
          <StepForward className="h-4 w-4" aria-hidden="true" /> Run next
        </button>
        <button className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-surface px-3 text-sm font-medium text-ink" onClick={pausePipeline} type="button">
          <Pause className="h-4 w-4" aria-hidden="true" /> Pause
        </button>
        <button className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-surface px-3 text-sm font-medium text-ink" onClick={resumePipeline} type="button">
          <Play className="h-4 w-4" aria-hidden="true" /> Resume
        </button>
        <button className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-surface px-3 text-sm font-medium text-ink" onClick={retryStage} type="button">
          <RotateCcw className="h-4 w-4" aria-hidden="true" /> Retry
        </button>
        <button className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-surface px-3 text-sm font-medium text-ink" onClick={cancelStageRun} type="button">
          <Square className="h-4 w-4" aria-hidden="true" /> Cancel
        </button>
        <button className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-surface px-3 text-sm font-medium text-ink" onClick={submitChange} type="button">
          <GitBranch className="h-4 w-4" aria-hidden="true" /> Submit change
        </button>
        <button className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-panel px-3 text-sm font-medium text-ink-muted" onClick={createSession} type="button">
          <Plus className="h-4 w-4" aria-hidden="true" /> New session
        </button>
      </div>
      <p className="mt-3 inline-flex items-center gap-2 text-sm text-ink-muted">
        <Check className="h-4 w-4 text-success" aria-hidden="true" />
        {state.message}
        {state.sessionId ? <span className="text-ink-subtle">Session {state.sessionId}</span> : null}
      </p>
    </div>
  );
}
