"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";

import { EscalateModal } from "@/components/EscalateModal";
import { IssueCard } from "@/components/IssueCard";
import { ResolveModal } from "@/components/ResolveModal";
import { EmptyState, ErrorState, InlineError, LoadingState } from "@/components/States";
import { api, errorMessage } from "@/lib/api";
import { pluralise } from "@/lib/format";
import { EvidenceType, Issue, IssueStatus } from "@/lib/types";

const ACTIONABLE: IssueStatus[] = ["OPEN", "IN_PROGRESS", "REOPENED"];

export default function HandlerPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [resolveTarget, setResolveTarget] = useState<Issue | null>(null);
  const [escalateTarget, setEscalateTarget] = useState<Issue | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const page = await api.getIssues({ scope: "assigned", limit: 100 });
      setIssues(page.items);
      setError(null);
    } catch (cause) {
      setError(cause);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const reload = useCallback(() => {
    setLoading(true);
    void load();
  }, [load]);

  const grouped = useMemo(() => {
    const open = issues.filter((issue) => ACTIONABLE.includes(issue.status));
    const waiting = issues.filter((issue) => issue.status === "RESOLVED_PENDING_VERIFICATION");
    const escalated = issues.filter((issue) => issue.status === "ESCALATED");
    const closed = issues.filter((issue) => issue.status === "VERIFIED_CLOSED");
    return { open, waiting, escalated, closed };
  }, [issues]);

  const startProgress = async (issue: Issue) => {
    setBusyId(issue.id);
    setActionError(null);
    try {
      await api.startProgress(issue.id);
      await load();
    } catch (cause) {
      setActionError(errorMessage(cause));
    } finally {
      setBusyId(null);
    }
  };

  const handleResolve = async (data: { evidence_type: EvidenceType; notes: string; attachment_url?: string }) => {
    if (!resolveTarget) return;
    await api.resolveIssue(resolveTarget.id, data);
    setResolveTarget(null);
    await load();
  };

  const handleEscalate = async (data: { reason: string; escalated_to_id?: number }) => {
    if (!escalateTarget) return;
    await api.escalateIssue(escalateTarget.id, data);
    setEscalateTarget(null);
    await load();
  };

  if (loading) return <LoadingState label="Loading your queue" />;
  if (error) return <ErrorState error={error} onRetry={reload} />;

  const actionButton = (issue: Issue) => (
    <>
      {issue.status === "OPEN" || issue.status === "REOPENED" ? (
        <button
          type="button"
          disabled={busyId === issue.id}
          onClick={() => void startProgress(issue)}
          className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-800 hover:bg-blue-100 disabled:opacity-50"
        >
          {busyId === issue.id ? "Starting…" : "Start work"}
        </button>
      ) : null}
      <button
        type="button"
        onClick={() => setResolveTarget(issue)}
        className="rounded-full border border-teal-200 bg-teal-50 px-3 py-1.5 text-xs font-semibold text-teal-800 hover:bg-teal-100"
      >
        Mark resolved
      </button>
      <button
        type="button"
        onClick={() => setEscalateTarget(issue)}
        className="rounded-full border border-purple-200 bg-purple-50 px-3 py-1.5 text-xs font-semibold text-purple-800 hover:bg-purple-100"
      >
        Escalate
      </button>
    </>
  );

  const section = (title: string, hint: string, items: Issue[], withActions: boolean) =>
    items.length === 0 ? null : (
      <section className="space-y-3">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-500">
            {title} <span className="ml-1 font-semibold text-gray-400">({items.length})</span>
          </h2>
          <p className="text-[11px] text-gray-400">{hint}</p>
        </div>
        <div className="grid gap-3">
          {items.map((issue) => (
            <IssueCard key={issue.id} issue={issue} actions={withActions ? actionButton(issue) : undefined} />
          ))}
        </div>
      </section>
    );

  return (
    <div className="space-y-7">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">My queue</h1>
        <p className="mt-1 text-sm text-gray-500">
          {pluralise(grouped.open.length, "issue")} needing your attention.
          Escalating is a judgement call, not a timer: use it when the work is genuinely
          outside what you can authorise.
        </p>
      </header>

      <InlineError message={actionError} />

      {issues.length === 0 ? (
        <EmptyState
          title="Nothing assigned to you"
          hint="Issues routed to you by the configured rules will appear here as students report them."
        />
      ) : (
        <>
          {section("Needs action", "Reported and waiting on you.", grouped.open, true)}
          {section("Awaiting student confirmation", "You marked these resolved. Students are confirming.", grouped.waiting, false)}
          {section("Escalated", "Passed to a higher authority with the full history.", grouped.escalated, false)}
          {section("Closed", "Confirmed fixed by the students who reported them.", grouped.closed, false)}
        </>
      )}

      <ResolveModal
        open={resolveTarget !== null}
        issue={resolveTarget}
        onClose={() => setResolveTarget(null)}
        onSubmit={handleResolve}
      />
      <EscalateModal
        open={escalateTarget !== null}
        issue={escalateTarget}
        onClose={() => setEscalateTarget(null)}
        onSubmit={handleEscalate}
      />
    </div>
  );
}
