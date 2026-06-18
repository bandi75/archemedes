"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, GitBranch, Pause, Play, Plus, RotateCcw, Square, StepForward } from "lucide-react";
import type { StageRow } from "@/lib/view-models";

const API_URL = process.env.NEXT_PUBLIC_ARCHIMEDES_API_URL ?? "http://localhost:8000/api/v1";

type SessionActionsProps = {
  sessionId: string;
  stages: StageRow[];
  selectedStage: StageRow;
};

type ActionState = {
  sessionId?: string;
  changeEventId?: string;
  currentStage?: string;
  stageRunId?: string;
  message: string;
};

export function SessionActions({ sessionId, stages, selectedStage }: SessionActionsProps) {
  const router = useRouter();
  const [state, setState] = useState<ActionState>({
    sessionId,
    currentStage: selectedStage.stage,
    stageRunId: selectedStage.stage_run_id ?? undefined,
    message: "Ready",
  });
  const failedStage = stages.find((stage) => stage.status === "failed");
  const runningStage = stages.find((stage) => stage.status === "running");
  const pausedStage = stages.find((stage) => stage.status === "paused");
  const nextStage = stages.find((stage) => !["completed", "skipped"].includes(stage.status));
  const requirementsDone = stages.some((stage) => stage.stage === "requirements_extraction" && stage.status === "completed");
  const optionsDone = stages.some((stage) => stage.stage === "options_generation" && stage.status === "completed");
  const allComplete = stages.every((stage) => ["completed", "skipped"].includes(stage.status));
  const canSubmitChange = requirementsDone || optionsDone || allComplete;
  const canPause = Boolean(runningStage);
  const canResume = Boolean(pausedStage);
  const canRetry = Boolean(failedStage);
  const canCancel = Boolean(runningStage || state.stageRunId);
  const primaryLabel = getPrimaryLabel({ failedStage, pausedStage, runningStage, nextStage, allComplete });
  const primaryDisabled = Boolean(runningStage || allComplete) && !failedStage && !pausedStage;

  async function runPrimary() {
    if (failedStage) {
      await retryStage();
      return;
    }
    if (pausedStage) {
      await resumePipeline();
      return;
    }
    await runStage();
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
        <button className={buttonClass("primary")} disabled={primaryDisabled} onClick={runPrimary} title="Runs the next eligible stage in this session." type="button">
          <StepForward className="h-4 w-4" aria-hidden="true" /> {primaryLabel}
        </button>
        <button className={buttonClass()} disabled={!canPause} onClick={pausePipeline} title={canPause ? "Pause after the current safe boundary." : "Available only while a stage is running."} type="button">
          <Pause className="h-4 w-4" aria-hidden="true" /> Pause
        </button>
        <button className={buttonClass()} disabled={!canResume} onClick={resumePipeline} title={canResume ? "Resume from the current or next eligible stage." : "Available only when the pipeline is paused."} type="button">
          <Play className="h-4 w-4" aria-hidden="true" /> Resume
        </button>
        <button className={buttonClass()} disabled={!canRetry} onClick={retryStage} title={canRetry ? "Retry the latest failed stage." : "Available only when a stage has failed."} type="button">
          <RotateCcw className="h-4 w-4" aria-hidden="true" /> Retry failed stage
        </button>
        <button className={buttonClass("danger")} disabled={!canCancel} onClick={cancelStageRun} title={canCancel ? "Cancel the current running stage/run." : "Available only while a run is active."} type="button">
          <Square className="h-4 w-4" aria-hidden="true" /> Cancel run
        </button>
        <button className={buttonClass()} disabled={!canSubmitChange} onClick={submitChange} title={canSubmitChange ? "Submit a requirement or design change for impact analysis." : "Available after initial requirements are captured."} type="button">
          <GitBranch className="h-4 w-4" aria-hidden="true" /> Submit change
        </button>
        <button className={buttonClass("secondary")} onClick={() => router.push("/sessions/new")} type="button">
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

function buttonClass(tone: "default" | "primary" | "secondary" | "danger" = "default") {
  const base = "inline-flex h-9 items-center gap-2 rounded-md border px-3 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-45";
  if (tone === "primary") {
    return `${base} border-accent bg-accent text-white hover:bg-ink`;
  }
  if (tone === "danger") {
    return `${base} border-danger/20 bg-surface text-danger hover:border-danger/40`;
  }
  if (tone === "secondary") {
    return `${base} border-border bg-panel text-ink-muted hover:text-ink`;
  }
  return `${base} border-border bg-surface text-ink hover:border-accent/40`;
}

function getPrimaryLabel({
  failedStage,
  pausedStage,
  runningStage,
  nextStage,
  allComplete,
}: {
  failedStage?: StageRow;
  pausedStage?: StageRow;
  runningStage?: StageRow;
  nextStage?: StageRow;
  allComplete: boolean;
}) {
  if (failedStage) {
    return "Retry failed stage";
  }
  if (pausedStage) {
    return "Resume";
  }
  if (runningStage) {
    return "View current stage";
  }
  if (allComplete) {
    return "Architecture package ready";
  }
  if (!nextStage || nextStage.stage === "intake") {
    return "Start intake";
  }
  return `Run ${nextStage.label.toLowerCase()}`;
}
