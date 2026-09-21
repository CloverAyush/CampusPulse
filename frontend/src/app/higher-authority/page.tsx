"use client";

import React, { useCallback, useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";

import { IssueCard } from "@/components/IssueCard";
import { ResolveModal } from "@/components/ResolveModal";
import { EmptyState, ErrorState, InlineError, LoadingState } from "@/components/States";
import { api, errorMessage } from "@/lib/api";
import { pluralise } from "@/lib/format";
import { EvidenceType, Issue, UserPublic } from "@/lib/types";

export default function HigherAuthorityPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [handlers, setHandlers] = useState<UserPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [resolveTarget, setResolveTarget] = useState<Issue | null>(null);
  const [reassigning, setReassigning] = useState<number | null>(null);

  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const [page, staff] = await Promise.all([
          api.getIssues({ scope: "escalated", limit: 100 }),
          api.listHandlers(),
        ]);
        if (cancelled) return;
        setIssues(page.items);
        setHandlers(staff);
        setError(null);
      } catch (cause) {
        if (!cancelled) setError(cause);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const reload = useCallback(() => {
    setLoading(true);
    setReloadToken((token) => token + 1);
  }, []);

  const handleReassign = async (issueId: number, handlerId: number) => {
    setReassigning(issueId);
    setActionError(null);
    try {
      await api.reassignIssue(issueId, { handler_id: handlerId });
      reload();
    } catch (cause) {
      setActionError(errorMessage(cause));
    } finally {
      setReassigning(null);
    }
  };

  const handleResolve = async (data: { evidence_type: EvidenceType; notes: string; attachment_url?: string }) => {
    if (!resolveTarget) return;
    await api.resolveIssue(resolveTarget.id, data);
    setResolveTarget(null);
    reload();
  };

  if (loading) return <LoadingState label="Loading escalations" />;
  if (error) return <ErrorState error={error} onRetry={reload} />;

  return (
    <div className="space-y-5">
      <header>
        <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
          <ShieldAlert className="h-6 w-6 text-purple-600" aria-hidden />
          Escalations
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          {pluralise(issues.length, "issue")} escalated to you. Each one arrives with its
          full history: every report, all evidence, and the handler&apos;s stated reason.
        </p>
      </header>

      <InlineError message={actionError} />

      {issues.length === 0 ? (
        <EmptyState
          title="No open escalations"
          hint="Handlers escalate an issue when resolving it is genuinely outside their authority."
        />
      ) : (
        <div className="grid gap-3">
          {issues.map((issue) => (
            <IssueCard
              key={issue.id}
              issue={issue}
              actions={
                <>
                  <button
                    type="button"
                    onClick={() => setResolveTarget(issue)}
                    className="rounded-full border border-teal-200 bg-teal-50 px-3 py-1.5 text-xs font-semibold text-teal-800 hover:bg-teal-100"
                  >
                    Record resolution
                  </button>
                  <label className="sr-only" htmlFor={`reassign-${issue.id}`}>
                    Reassign this issue
                  </label>
                  <select
                    id={`reassign-${issue.id}`}
                    disabled={reassigning === issue.id}
                    value=""
                    onChange={(event) => {
                      if (event.target.value) void handleReassign(issue.id, Number(event.target.value));
                    }}
                    className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 focus:border-indigo-400 focus:outline-none disabled:opacity-50"
                  >
                    <option value="">Reassign to…</option>
                    {handlers
                      .filter((handler) => handler.id !== issue.current_handler_id)
                      .map((handler) => (
                        <option key={handler.id} value={handler.id}>
                          {handler.full_name}
                        </option>
                      ))}
                  </select>
                </>
              }
            />
          ))}
        </div>
      )}

      <ResolveModal
        open={resolveTarget !== null}
        issue={resolveTarget}
        onClose={() => setResolveTarget(null)}
        onSubmit={handleResolve}
      />
    </div>
  );
}
