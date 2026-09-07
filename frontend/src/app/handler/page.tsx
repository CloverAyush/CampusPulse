"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Issue, IssueStatus, User, EvidenceType } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";
import { ResolveModal } from "@/components/ResolveModal";
import { EscalateModal } from "@/components/EscalateModal";
import {
  Wrench,
  PlayCircle,
  CheckCircle2,
  AlertOctagon,
  RefreshCw,
  MapPin,
  Users,
  Clock,
  ArrowRight,
  Filter,
  CheckCircle,
} from "lucide-react";

export default function HandlerQueuePage() {
  const { user } = useAuth();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [authorities, setAuthorities] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Modals state
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  const [isResolveOpen, setIsResolveOpen] = useState(false);
  const [isEscalateOpen, setIsEscalateOpen] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [issuesData, authsData] = await Promise.all([
        api.getIssues(),
        api.listUsers("higher_authority"),
      ]);
      setIssues(issuesData);
      setAuthorities(authsData);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [user]);

  const handleStartProgress = async (issueId: number) => {
    try {
      await api.startProgress(issueId);
      setToastMsg("Status updated to In Progress. Student reporters have been notified.");
      loadData();
      setTimeout(() => setToastMsg(null), 3000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to start progress");
    }
  };

  const handleResolveSubmit = async (data: {
    evidence_type: EvidenceType;
    notes: string;
    attachment_url?: string;
  }) => {
    if (!selectedIssue) return;
    await api.resolveIssue(selectedIssue.id, data);
    setToastMsg("Resolution & proof recorded successfully!");
    loadData();
    setTimeout(() => setToastMsg(null), 3000);
  };

  const handleEscalateSubmit = async (data: {
    reason: string;
    escalated_to_id?: number;
  }) => {
    if (!selectedIssue) return;
    await api.escalateIssue(selectedIssue.id, data);
    setToastMsg("Issue escalated to higher authority with full case snapshot.");
    loadData();
    setTimeout(() => setToastMsg(null), 3000);
  };

  const filteredIssues = issues.filter((i) => {
    if (statusFilter === "ALL") return true;
    return i.status === statusFilter;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2.5">
            <Wrench className="w-6 h-6 text-blue-600" />
            <span>Assigned Issues Queue</span>
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Deterministic routing inbox for <strong>{user?.full_name}</strong> ({user?.department || "Campus Operations"}).
          </p>
        </div>

        <button
          onClick={loadData}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 border border-gray-200 rounded-xl shadow-sm transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Queue</span>
        </button>
      </div>

      {toastMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center gap-3 text-xs text-emerald-800 font-medium animate-in fade-in">
          <CheckCircle className="w-5 h-5 shrink-0 text-emerald-600" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 p-1.5 bg-gray-100 rounded-2xl w-fit">
        {[
          { key: "ALL", label: "All Assigned" },
          { key: "OPEN", label: "Open / Routed" },
          { key: "IN_PROGRESS", label: "In Progress" },
          { key: "REOPENED", label: "Reopened / Disputed" },
          { key: "RESOLVED_PENDING_VERIFICATION", label: "Pending Verification" },
          { key: "VERIFIED_CLOSED", label: "Closed" },
        ].map((tab) => {
          const count =
            tab.key === "ALL"
              ? issues.length
              : issues.filter((i) => i.status === tab.key).length;

          return (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 ${
                statusFilter === tab.key
                  ? "bg-white text-indigo-900 shadow-sm font-bold"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              <span>{tab.label}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  statusFilter === tab.key
                    ? "bg-indigo-100 text-indigo-800 font-bold"
                    : "bg-gray-200 text-gray-600"
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Queue Cards */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-40 bg-white rounded-3xl border border-gray-200 animate-pulse" />
          ))}
        </div>
      ) : filteredIssues.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-gray-200 space-y-2">
          <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
          <h3 className="text-base font-bold text-gray-900">Queue is Clear</h3>
          <p className="text-xs text-gray-500">
            No issues found matching the selected filter status.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredIssues.map((issue) => {
            const canStart = issue.status === "OPEN" || issue.status === "REOPENED";
            const canResolve =
              issue.status === "IN_PROGRESS" ||
              issue.status === "OPEN" ||
              issue.status === "REOPENED";
            const canEscalate =
              issue.status !== "ESCALATED" &&
              issue.status !== "VERIFIED_CLOSED";

            return (
              <div
                key={issue.id}
                className="p-6 bg-white rounded-3xl border border-gray-200/90 shadow-sm hover:border-blue-300 transition-all space-y-4"
              >
                {/* Card Top */}
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-full">
                        {issue.issue_type?.category} &rarr; {issue.issue_type?.sub_type}
                      </span>
                      {issue.specific_asset && (
                        <span className="text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full font-medium">
                          Asset: {issue.specific_asset}
                        </span>
                      )}
                      <span className="text-xs text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        <span>{issue.report_count} linked report(s)</span>
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-gray-900">
                      {issue.title}
                    </h3>
                  </div>

                  <StatusBadge status={issue.status} />
                </div>

                {/* Problem Description */}
                <p className="text-xs text-gray-700 leading-relaxed bg-slate-50 p-3 rounded-2xl border border-slate-100">
                  {issue.description}
                </p>

                {/* Footer Controls */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-2 text-xs border-t border-gray-100">
                  <div className="flex items-center gap-4 text-gray-500">
                    <div className="flex items-center gap-1.5 font-medium">
                      <MapPin className="w-3.5 h-3.5 text-gray-400" />
                      <span>{issue.location?.name}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-[11px] text-gray-400">
                      <Clock className="w-3.5 h-3.5" />
                      <span>Received {new Date(issue.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-wrap items-center gap-2">
                    {canStart && (
                      <button
                        type="button"
                        onClick={() => handleStartProgress(issue.id)}
                        className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl shadow-sm transition-all"
                      >
                        <PlayCircle className="w-3.5 h-3.5" />
                        <span>Start Working</span>
                      </button>
                    )}

                    {canResolve && (
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedIssue(issue);
                          setIsResolveOpen(true);
                        }}
                        className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs rounded-xl shadow-sm transition-all"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Resolve + Evidence</span>
                      </button>
                    )}

                    {canEscalate && (
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedIssue(issue);
                          setIsEscalateOpen(true);
                        }}
                        className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 font-semibold text-xs rounded-xl transition-all"
                      >
                        <AlertOctagon className="w-3.5 h-3.5 text-purple-600" />
                        <span>Escalate...</span>
                      </button>
                    )}

                    <Link
                      href={`/issues/${issue.id}`}
                      className="inline-flex items-center gap-1 px-3 py-2 text-xs font-semibold text-gray-600 hover:text-indigo-600 hover:bg-gray-100 rounded-xl transition-colors"
                    >
                      <span>History</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Resolve Modal */}
      <ResolveModal
        isOpen={isResolveOpen}
        issueTitle={selectedIssue?.title || ""}
        requiresVerification={selectedIssue?.requires_verification ?? true}
        onClose={() => setIsResolveOpen(false)}
        onSubmit={handleResolveSubmit}
      />

      {/* Escalate Modal */}
      <EscalateModal
        isOpen={isEscalateOpen}
        issueTitle={selectedIssue?.title || ""}
        authorities={authorities}
        onClose={() => setIsEscalateOpen(false)}
        onSubmit={handleEscalateSubmit}
      />
    </div>
  );
}

