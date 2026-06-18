"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";

const API_URL = process.env.NEXT_PUBLIC_ARCHIMEDES_API_URL ?? "http://localhost:8000/api/v1";

const demoNeed = "Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability.";

export default function NewSessionPage() {
  const router = useRouter();
  const [title, setTitle] = useState("Fintech fraud platform");
  const [businessNeed, setBusinessNeed] = useState(demoNeed);
  const [status, setStatus] = useState("Ready to create draft session");

  async function createSession() {
    if (!businessNeed.trim()) {
      setStatus("Business need is required");
      return;
    }
    try {
      const response = await fetch(`${API_URL}/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title.trim() || undefined,
          business_need: businessNeed,
        }),
      });
      const payload = await response.json();
      setStatus(`Session created: ${payload.session_id}. Redirecting to Pipeline.`);
      router.push("/pipeline");
    } catch {
      setStatus("API unavailable; showing mock Pipeline next.");
      router.push("/pipeline");
    }
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Command Center", "New Session"]}
          title="New architecture session"
          description="Create the session container with the minimum context needed. Intake will run as Stage 1 from Pipeline."
          badges={[
            { label: "No session created yet", variant: "neutral" },
            { label: "Creation mode", variant: "info" },
          ]}
        />

        <section className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.75fr)]">
          <div className="rounded-lg border border-border bg-panel p-5 shadow-panel">
            <h2 className="text-base font-semibold text-ink">Session basics</h2>
            <label className="mt-5 block text-sm font-medium text-ink" htmlFor="session-title">Session title</label>
            <input
              id="session-title"
              className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Optional. Archimedes can infer a title later."
              value={title}
            />
            <label className="mt-5 block text-sm font-medium text-ink" htmlFor="business-need">Business need</label>
            <textarea
              id="business-need"
              className="mt-2 min-h-40 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm leading-6 text-ink outline-none transition focus:border-accent"
              onChange={(event) => setBusinessNeed(event.target.value)}
              required
              value={businessNeed}
            />
            <div className="mt-5 flex flex-wrap gap-2">
              <button className="inline-flex h-10 items-center rounded-md bg-accent px-4 text-sm font-semibold text-white transition hover:bg-ink" onClick={createSession} type="button">
                Create session
              </button>
              <button className="inline-flex h-10 items-center rounded-md border border-border bg-surface px-4 text-sm font-semibold text-ink" onClick={() => router.push("/")} type="button">
                Cancel
              </button>
              <button className="inline-flex h-10 items-center rounded-md border border-border bg-panel px-4 text-sm font-semibold text-ink-muted" onClick={() => setBusinessNeed(demoNeed)} type="button">
                Use demo template
              </button>
            </div>
            <p className="mt-3 text-sm text-ink-muted">{status}</p>
          </div>

          <aside className="space-y-5">
            <div className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <h2 className="text-base font-semibold text-ink">Creation defaults</h2>
              <div className="mt-4 space-y-3 text-sm text-ink-muted">
                <p><span className="font-medium text-ink">Domain:</span> Auto-detect / Financial services</p>
                <p><span className="font-medium text-ink">Preferred cloud:</span> Azure</p>
                <p><span className="font-medium text-ink">Library context:</span> Org approved services v2.1</p>
                <p><span className="font-medium text-ink">Evidence sources:</span> Default architecture KB</p>
              </div>
            </div>
            <div className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <h2 className="text-base font-semibold text-ink">Prompt readiness</h2>
              <div className="mt-4 flex flex-wrap gap-2">
                {["Business goal", "Scale", "Compliance", "Availability"].map((item) => (
                  <StatusBadge key={item} variant="success">{item}</StatusBadge>
                ))}
                <StatusBadge variant="warning">Data boundary later</StatusBadge>
              </div>
              <p className="mt-4 text-sm leading-6 text-ink-muted">Clarifying questions belong to the Intake stage after the session exists.</p>
            </div>
          </aside>
        </section>
      </div>
    </AppShell>
  );
}
