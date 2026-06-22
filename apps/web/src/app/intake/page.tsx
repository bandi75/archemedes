"use client";

import Link from "next/link";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";

const API_URL = process.env.NEXT_PUBLIC_ARCHIMEDES_API_URL ?? "http://localhost:8000/api/v1";

const originalNeed =
  "Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability.";

const refinedNeed =
  "Design an Azure-first real-time fraud detection platform for fintech card transactions, with PCI-DSS boundaries, high-throughput ingestion, evidence-backed service choices, and explicit availability targets.";

const openQuestions = [
  "What is the target p95/p99 scoring latency?",
  "Is cardholder data tokenized before ingestion?",
  "Is active-active multi-region required in v1 or later?",
  "Are there approved or prohibited services we must honor?",
];

const checklist = [
  ["Business goal", "complete", "success"],
  ["Scale", "complete", "success"],
  ["Compliance", "complete", "success"],
  ["Availability", "complete", "success"],
  ["Latency", "needs detail", "warning"],
  ["Data boundary", "needs validation", "warning"],
] as const;

export default function IntakePage() {
  const [answers, setAnswers] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [ready, setReady] = useState(false);
  const [status, setStatus] = useState("Waiting for clarification answers.");
  const [sessionId, setSessionId] = useState<string | null>(() => getSessionIdFromBrowser());
  const hasOpenQuestions = openQuestions.length > 0 && !submitted;

  async function resolveActiveSessionId() {
    if (sessionId) {
      if (typeof window !== "undefined") {
        window.localStorage.setItem("archimedes.activeSessionId", sessionId);
      }
      return sessionId;
    }

    const browserSessionId = getSessionIdFromBrowser();
    if (browserSessionId) {
      setSessionId(browserSessionId);
      if (typeof window !== "undefined") {
        window.localStorage.setItem("archimedes.activeSessionId", browserSessionId);
      }
      return browserSessionId;
    }

    const response = await fetch(`${API_URL}/sessions`, { cache: "no-store" });
    if (!response.ok) {
      throw new Error("session_lookup_failed");
    }
    const payload = (await response.json()) as { items?: Array<{ session_id?: string }> };
    const latestSessionId = payload.items?.[0]?.session_id ?? null;
    if (latestSessionId && typeof window !== "undefined") {
      setSessionId(latestSessionId);
      window.localStorage.setItem("archimedes.activeSessionId", latestSessionId);
    }
    return latestSessionId;
  }

  async function submitAnswers() {
    if (!answers.trim()) {
      setStatus("Add clarification answers before submitting.");
      return;
    }

    setSubmitting(true);
    setStatus("Submitting clarification answers...");
    try {
      const resolvedSessionId = await resolveActiveSessionId();
      if (!resolvedSessionId) {
        setStatus("No active session found. Create a session first, then submit the intake answers.");
        return;
      }

      const response = await fetch(`${API_URL}/sessions/${resolvedSessionId}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": `intake-clarifications-${resolvedSessionId}-${Date.now()}`,
        },
        body: JSON.stringify({
          message: `Intake clarification answers:\n${answers}`,
        }),
      });
      if (!response.ok) {
        throw new Error("clarification_submit_failed");
      }
      setSubmitted(true);
      setStatus("Clarification answers submitted to Archimedes. Intake can now be marked ready.");
    } catch {
      setStatus("Could not submit answers to the API. Check that FastAPI is running and CORS is enabled for this UI.");
    } finally {
      setSubmitting(false);
    }
  }

  async function markReady() {
    if (!submitted) {
      setStatus("Submit clarification answers before marking Intake ready.");
      return;
    }
    setReady(true);
    setStatus("Intake ready for requirements extraction. Return to Pipeline to run the next stage.");
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Session Workspace", "Intake"]}
          title="Intake Stage Detail"
          description="Review the business need, answer intake clarifications, confirm library context, and prepare the session for requirements extraction."
          badges={[{ label: "Stage 1", variant: "info" }]}
        />
        <SessionContextCard ready={ready} />
        <section className="rounded-lg border border-border bg-panel p-4 shadow-panel">
          <div className="flex flex-wrap gap-2">
            <button
              className="inline-flex h-9 items-center rounded-md border border-border bg-surface px-3 text-sm font-medium text-ink"
              type="button"
            >
              Edit business need
            </button>
            <button
              className="inline-flex h-9 items-center rounded-md bg-accent px-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
              disabled={submitting}
              onClick={submitAnswers}
              type="button"
            >
              {submitting ? "Submitting..." : "Submit clarification answers"}
            </button>
            <button
              className="inline-flex h-9 items-center rounded-md border border-border bg-surface px-3 text-sm font-medium text-ink disabled:cursor-not-allowed disabled:opacity-50"
              disabled={hasOpenQuestions}
              onClick={markReady}
              title={hasOpenQuestions ? "Answer required clarifications first." : "Ready for requirements extraction."}
              type="button"
            >
              Mark ready for requirements
            </button>
            <Link
              className="inline-flex h-9 items-center rounded-md border border-border bg-surface px-3 text-sm font-medium text-ink"
              href="/pipeline"
            >
              Back to pipeline
            </Link>
          </div>
          <p className="mt-3 text-sm text-ink-muted" role="status">
            {status}
          </p>
        </section>

        <section className="grid gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(340px,0.65fr)]">
          <main className="space-y-5">
            <InfoCard title="Original business need" body={originalNeed} />
            <InfoCard title="Refined business need" body={refinedNeed} accent />

            <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <h2 className="text-base font-semibold text-ink">Open clarifications</h2>
              <div className="mt-4 space-y-3">
                {openQuestions.map((question, index) => (
                  <div key={question} className="rounded-md border border-border bg-surface p-3">
                    <p className="text-sm font-medium text-ink">
                      {index + 1}. {question}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <h2 className="text-base font-semibold text-ink">Your response</h2>
              <label className="mt-4 block text-sm font-medium text-ink" htmlFor="clarification-response">
                Clarification answers
              </label>
              <textarea
                className="mt-2 min-h-36 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm leading-6 text-ink outline-none transition focus:border-accent"
                id="clarification-response"
                onChange={(event) => setAnswers(event.target.value)}
                placeholder="Answer the questions above, paste extra constraints, or refine details Archimedes should consider before requirements extraction..."
                value={answers}
              />
              <button
                className="mt-4 inline-flex h-10 items-center rounded-md bg-accent px-4 text-sm font-semibold text-white transition hover:bg-ink disabled:cursor-not-allowed disabled:opacity-50"
                disabled={submitting}
                onClick={submitAnswers}
                type="button"
              >
                {submitting ? "Submitting..." : "Submit answers"}
              </button>
              <p className="mt-3 text-sm text-ink-muted" role="status">
                {status}
              </p>
            </section>

            <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <h2 className="text-base font-semibold text-ink">Intake notes and assumptions</h2>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                {[
                  "PCI-DSS scope depends on upstream tokenization boundary.",
                  "10K TPS is the current baseline; higher scale may trigger re-reasoning later.",
                  "Azure managed services are preferred unless prohibited by org policy.",
                  "Availability target is known, but latency target needs more detail.",
                ].map((note) => (
                  <p key={note} className="rounded-md border border-border bg-surface p-3 text-sm leading-6 text-ink-muted">
                    {note}
                  </p>
                ))}
              </div>
            </section>
          </main>

          <aside className="space-y-5">
            <div className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <h2 className="text-base font-semibold text-ink">Session setup</h2>
              <div className="mt-4 space-y-3 text-sm text-ink-muted">
                <SetupRow label="Domain" value="Financial services" source="inferred" />
                <SetupRow label="Preferred cloud" value="Azure" source="user provided" />
                <SetupRow label="Library context" value="Org services v2.1" source="default" />
                <SetupRow label="Evidence sources" value="Architecture KB, WAF, internal standards" source="default" />
              </div>
            </div>

            <div className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <h2 className="text-base font-semibold text-ink">Intake readiness</h2>
              <div className="mt-4 space-y-3">
                {checklist.map(([label, state, variant]) => (
                  <div
                    key={label}
                    className="flex items-center justify-between gap-3 rounded-md border border-border bg-surface p-3"
                  >
                    <span className="text-sm font-medium text-ink">{label}</span>
                    <StatusBadge variant={variant}>{state}</StatusBadge>
                  </div>
                ))}
                <div className="flex items-center justify-between gap-3 rounded-md border border-border bg-surface p-3">
                  <span className="text-sm font-medium text-ink">Clarification answers</span>
                  <StatusBadge variant={submitted ? "success" : "warning"}>
                    {submitted ? "submitted" : "needed"}
                  </StatusBadge>
                </div>
                <div className="flex items-center justify-between gap-3 rounded-md border border-border bg-surface p-3">
                  <span className="text-sm font-medium text-ink">Ready for requirements</span>
                  <StatusBadge variant={ready ? "success" : "neutral"}>{ready ? "ready" : "not yet"}</StatusBadge>
                </div>
              </div>
            </div>
          </aside>
        </section>
      </div>
    </AppShell>
  );
}

function getSessionIdFromBrowser(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const params = new URLSearchParams(window.location.search);
  return params.get("sessionId") ?? window.localStorage.getItem("archimedes.activeSessionId");
}

function SessionContextCard({ ready }: { ready: boolean }) {
  return (
    <section className="rounded-lg border border-border bg-panel px-5 py-4 shadow-panel">
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-subtle">Current session</p>
      <h2 className="mt-1 text-base font-semibold text-ink">Fintech fraud platform</h2>
      <div className="mt-2 flex flex-wrap gap-2">
        <StatusBadge variant="info">Current stage: Intake</StatusBadge>
        <StatusBadge variant="neutral">Active version: v0</StatusBadge>
        <StatusBadge variant="neutral">Owner: current user</StatusBadge>
        <StatusBadge variant={ready ? "success" : "warning"}>
          {ready ? "Pipeline status: Intake ready" : "Pipeline status: Waiting for intake readiness"}
        </StatusBadge>
      </div>
    </section>
  );
}

function InfoCard({ title, body, accent = false }: { title: string; body: string; accent?: boolean }) {
  return (
    <section
      className={
        accent
          ? "rounded-lg border border-accent/20 bg-accent/5 p-5 shadow-panel"
          : "rounded-lg border border-border bg-panel p-5 shadow-panel"
      }
    >
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      <p className="mt-4 text-sm leading-6 text-ink-muted">{body}</p>
    </section>
  );
}

function SetupRow({ label, value, source }: { label: string; value: string; source: string }) {
  return (
    <div className="rounded-md border border-border bg-surface p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-ink">{label}</p>
          <p className="mt-1 text-sm text-ink-muted">{value}</p>
        </div>
        <StatusBadge variant="neutral">{source}</StatusBadge>
      </div>
    </div>
  );
}
