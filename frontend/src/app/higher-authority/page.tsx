"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Issue, User, EvidenceType } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";
import { ResolveModal } from "@/components/ResolveModal";
import {
  ShieldAlert,
  AlertOctagon,
  RefreshCw,
  MapPin,
  Users,
  CheckCircle2,
  RefreshCcw,
  ArrowRight,
  ShieldCheck,
  CheckCircle,
} from "lucide-react";

export default function HigherAuthorityPage() {
  const { user } = useAuth();
  const [escalatedIssues, setEscalatedIssues] = useState<Issue[]>([]);
  const [handlers, setHandlers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  // Resolution & Reassign Modals
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  const [isResolveOpen, setIsResolveOpen] = useState(false);
  const [isReassignOpen, setIsReassignOpen] = useState(false);
  const [reassignHandlerId, setReassignHandlerId] = useState<number | null>(null);
  const [reassignReason, setReassignReason] = useState("");
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [issuesData, handlersData] = await Promise.all([
        api.getIssues("ESCALATED"),
        api.listUsers("handler"),
      ]);
      setEscalatedIssues(issuesData);
      setHandlers(handlersData);
      if (handlersData.length > 0) setReassignHandlerId(handlersData[0].id);
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

  const handleResolveSubmit = async (data: {
    evidence_type: EvidenceType;
    notes: string;
    attachment_url?: string;
  }) => {
    if (!selectedIssue) return;
    await api.resolveIssue(selectedIssue.id, data);
    setToastMsg("Escalated issue resolved with executive proof.");
    loadData();
    setTimeout(() => setToastMsg(null), 3000);
  };

  const handleReassignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIssue || !reassignHandlerId) return;
    try {
      await api.reassignIssue(selectedIssue.id, {
        handler_id: reassignHandlerId,
        reason: reassignReason || undefined,
      });
      setIsReassignOpen(false);
      setToastMsg("Issue reassigned to new handler successfully.");
      loadData();
      setTimeout(() => setToastMsg(null), 3000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to reassign");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2.5">
            <ShieldAlert className="w-6 h-6 text-purple-600" />
            <span>Escalated Issues Authority Queue</span>
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Reviewing escalated campus problems requiring higher administrative intervention.
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

      {/* Info Banner */}
      <div className="bg-purple-900 text-white p-6 rounded-3xl shadow-xl flex items-start gap-4">
        <div className="p-3 bg-purple-700/80 rounded-2xl">
          <AlertOctagon className="w-6 h-6 text-purple-200" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-bold">Complete Case Transparency Principle</h3>
          <p className="text-xs text-purple-200 leading-relaxed max-w-3xl">
            Every escalated issue in this queue carries its full case history: all original student
            submissions, photos, the assigned handler who escalated it, and their stated justification.
            Nothing is summarized away.
          </p>
        </div>
      </div>

      {/* Escalated Queue */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((n) => (
            <div key={n} className="h-44 bg-white rounded-3xl border border-gray-200 animate-pulse" />
          ))}
        </div>
      ) : escalatedIssues.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-gray-200 space-y-2">
          <ShieldCheck className="w-10 h-10 text-emerald-500 mx-auto" />
          <h3 className="text-base font-bold text-gray-900">No Escalated Issues Pending</h3>
          <p className="text-xs text-gray-500">
            All campus issues are being resolved within operational tiers or have been completed.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {escalatedIssues.map((issue) => (
            <div
              key={issue.id}
              className="p-6 bg-white rounded-3xl border-2 border-purple-200 shadow-md space-y-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-bold text-purple-800 bg-purple-50 px-2.5 py-0.5 rounded-full">
                      {issue.issue_type?.category} &rarr; {issue.issue_type?.sub_type}
                    </span>
                    <span className="text-xs text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      <span>{issue.report_count} student report(s)</span>
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-gray-900">
                    {issue.title}
                  </h3>
                </div>

                <StatusBadge status={issue.status} />
              </div>

              <p className="text-xs text-gray-700 leading-relaxed bg-slate-50 p-3 rounded-2xl border border-slate-100">
                {issue.description}
              </p>

              {/* Action Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-gray-100 text-xs">
                <div className="flex items-center gap-4 text-gray-500">
                  <div className="flex items-center gap-1.5 font-medium">
                    <MapPin className="w-3.5 h-3.5 text-gray-400" />
                    <span>{issue.location?.name}</span>
                  </div>
                  {issue.current_handler && (
                    <div className="text-[11px] text-gray-600 bg-gray-100 px-2.5 py-0.5 rounded-full">
                      Escalated by: <strong>{issue.current_handler.full_name}</strong>
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedIssue(issue);
                      setIsResolveOpen(true);
                    }}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs rounded-xl shadow-sm transition-all"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Executive Resolution</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setSelectedIssue(issue);
                      setIsReassignOpen(true);
                    }}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 font-semibold text-xs rounded-xl transition-all"
                  >
                    <RefreshCcw className="w-3.5 h-3.5 text-amber-700" />
                    <span>Reassign Staff</span>
                  </button>

                  <Link
                    href={`/issues/${issue.id}`}
                    className="inline-flex items-center gap-1 px-3 py-2 text-xs font-semibold text-purple-700 bg-purple-50 hover:bg-purple-100 rounded-xl transition-colors"
                  >
                    <span>Inspect Full Timeline</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Executive Resolve Modal */}
      <ResolveModal
        isOpen={isResolveOpen}
        issueTitle={selectedIssue?.title || ""}
        requiresVerification={selectedIssue?.requires_verification ?? true}
        onClose={() => setIsResolveOpen(false)}
        onSubmit={handleResolveSubmit}
      />

      {/* Reassign Modal */}
      {isReassignOpen && selectedIssue && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full p-6 space-y-4 border border-gray-100">
            <h3 className="text-base font-bold text-gray-900">Reassign Issue Handler</h3>
            <p className="text-xs text-gray-500">{selectedIssue.title}</p>

            <form onSubmit={handleReassignSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Select New Responsible Staff
                </label>
                <select
                  value={reassignHandlerId || ""}
                  onChange={(e) => setReassignHandlerId(Number(e.target.value))}
                  className="w-full text-xs p-3 border border-gray-200 rounded-xl outline-none bg-white font-medium"
                >
                  {handlers.map((h) => (
                    <option key={h.id} value={h.id}>
                      {h.full_name} ({h.department || "Handler"})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Reassignment Reason / Guidance Note
                </label>
                <textarea
                  rows={3}
                  value={reassignReason}
                  onChange={(e) => setReassignReason(e.target.value)}
                  placeholder="E.g., Budget approved under Deanery Fund #104. Reassigning to IT lead for vendor procurement."
                  className="w-full text-xs p-3 border border-gray-200 rounded-xl outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setIsReassignOpen(false)}
                  className="px-4 py-2 text-xs font-medium text-gray-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md"
                >
                  Confirm Reassignment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

