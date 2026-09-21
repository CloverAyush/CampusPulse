"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { PlusCircle } from "lucide-react";

import { IssueCard } from "@/components/IssueCard";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { api } from "@/lib/api";
import { pluralise } from "@/lib/format";
import { Issue, IssueScope, IssueStatus } from "@/lib/types";

const VIEWS: { scope: Extract<IssueScope, "mine" | "all">; label: string; hint: string }[] = [
  { scope: "mine", label: "My reports", hint: "Issues you reported or joined" },
  { scope: "all", label: "All campus issues", hint: "Everything currently reported across campus" },
];

const STATUS_FILTERS: { value: IssueStatus | ""; label: string }[] = [
  { value: "", label: "All" },
  { value: "OPEN", label: "Open" },
  { value: "IN_PROGRESS", label: "In progress" },
  { value: "ESCALATED", label: "Escalated" },
  { value: "RESOLVED_PENDING_VERIFICATION", label: "Awaiting confirmation" },
  { value: "VERIFIED_CLOSED", label: "Closed" },
];

export default function IssuesPage() {
  const [scope, setScope] = useState<"mine" | "all">("mine");
  const [statusFilter, setStatusFilter] = useState<IssueStatus | "">("");
  const [issues, setIssues] = useState<Issue[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const page = await api.getIssues({
          scope,
          status: statusFilter || undefined,
          limit: 50,
        });
        if (cancelled) return;
        setIssues(page.items);
        setTotal(page.total);
        setError(null);
      } catch (cause) {
        if (!cancelled) setError(cause);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    // Switching tabs quickly would otherwise let a slow first response land on top
    // of a newer one, showing the wrong list under the selected tab.
    return () => {
      cancelled = true;
    };
  }, [scope, statusFilter, reloadToken]);

  const reload = useCallback(() => {
    setLoading(true);
    setReloadToken((token) => token + 1);
  }, []);

  const activeView = VIEWS.find((view) => view.scope === scope);

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Issues</h1>
          <p className="mt-1 text-sm text-gray-500">{activeView?.hint}</p>
        </div>
        <Link
          href="/report"
          className="inline-flex items-center gap-1.5 rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          <PlusCircle className="h-4 w-4" aria-hidden />
          Report an issue
        </Link>
      </header>

      <div className="flex flex-wrap items-center gap-3">
        <div className="inline-grid grid-cols-2 gap-1 rounded-full bg-gray-100 p-1" role="tablist" aria-label="Which issues to show">
          {VIEWS.map((view) => (
            <button
              key={view.scope}
              type="button"
              role="tab"
              aria-selected={scope === view.scope}
              onClick={() => {
                setLoading(true);
                setScope(view.scope);
              }}
              className={`rounded-full px-4 py-1.5 text-sm font-semibold transition ${
                scope === view.scope ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-800"
              }`}
            >
              {view.label}
            </button>
          ))}
        </div>

        <label className="ml-auto flex items-center gap-2 text-xs text-gray-500">
          Status
          <select
            value={statusFilter}
            onChange={(event) => {
              setLoading(true);
              setStatusFilter(event.target.value as IssueStatus | "");
            }}
            className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs focus:border-indigo-400 focus:outline-none"
          >
            {STATUS_FILTERS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading ? (
        <LoadingState label="Loading issues" />
      ) : error ? (
        <ErrorState error={error} onRetry={reload} />
      ) : issues.length === 0 ? (
        <EmptyState
          title={scope === "mine" ? "You have not reported anything yet" : "Nothing is currently reported"}
          hint={
            scope === "mine"
              ? "When you report a problem it will appear here, along with everything that happens to it."
              : "Either the campus is in unusually good shape, or nobody has reported anything yet."
          }
          action={
            <Link href="/report" className="rounded-full bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700">
              Report an issue
            </Link>
          }
        />
      ) : (
        <>
          <p className="text-xs text-gray-400">{pluralise(total, "issue")}</p>
          <div className="grid gap-3">
            {issues.map((issue) => (
              <IssueCard key={issue.id} issue={issue} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
