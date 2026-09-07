"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Issue, Report, ResolutionEvidence, VerificationStatus } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";
import { VerifyModal } from "@/components/VerifyModal";
import {
  FileText,
  MapPin,
  Clock,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  PlusCircle,
} from "lucide-react";

export default function MyReportsPage() {
  const { user } = useAuth();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [myReports, setMyReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  // Verification Modal State
  const [selectedIssueForVerify, setSelectedIssueForVerify] = useState<Issue | null>(null);
  const [verifyEvidence, setVerifyEvidence] = useState<ResolutionEvidence | null>(null);
  const [isVerifyOpen, setIsVerifyOpen] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [issuesData, reportsData] = await Promise.all([
        api.getIssues(),
        api.getMyReports(),
      ]);
      setIssues(issuesData);
      setMyReports(reportsData);
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

  const handleOpenVerify = async (issue: Issue) => {
    setSelectedIssueForVerify(issue);
    try {
      const detail = await api.getIssue(issue.id);
      if (detail.evidences && detail.evidences.length > 0) {
        setVerifyEvidence(detail.evidences[0]);
      } else {
        setVerifyEvidence(null);
      }
    } catch {
      setVerifyEvidence(null);
    }
    setIsVerifyOpen(true);
  };

  const handleVerifySubmit = async (data: {
    status: VerificationStatus;
    comment?: string;
  }) => {
    if (!selectedIssueForVerify) return;
    await api.verifyIssue(selectedIssueForVerify.id, data);
    setActionSuccess(
      data.status === "confirmed"
        ? "Resolution confirmed! The issue has been officially verified and closed."
        : "Dispute submitted! The issue has been reopened and the handler notified."
    );
    loadData();
    setTimeout(() => setActionSuccess(null), 4000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-indigo-600" />
            <span>My Submitted Reports & Issues</span>
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Track status of campus problems you reported and verify resolutions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-xl transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <Link
            href="/report"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-indigo-500/20 transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Report</span>
          </Link>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center gap-3 text-xs text-emerald-800 font-medium animate-in fade-in">
          <CheckCircle className="w-5 h-5 shrink-0 text-emerald-600" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Issues Requiring Verification Banner */}
      {issues.some((i) => i.status === "RESOLVED_PENDING_VERIFICATION") && (
        <div className="p-5 bg-gradient-to-r from-teal-500/10 via-emerald-500/10 to-teal-500/10 border-2 border-teal-500/30 rounded-3xl space-y-3">
          <div className="flex items-center gap-2 text-teal-900 font-bold text-sm">
            <ShieldCheck className="w-5 h-5 text-teal-600" />
            <span>Action Needed: Verify Handler Resolution</span>
          </div>
          <p className="text-xs text-teal-800 leading-relaxed">
            One or more of your reported issues has been marked fixed by staff. Please inspect the location
            and confirm if it is working properly, or dispute if it is still broken.
          </p>
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-32 bg-white rounded-3xl border border-gray-200 animate-pulse" />
          ))}
        </div>
      ) : issues.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-gray-200 space-y-3">
          <FileText className="w-10 h-10 text-gray-300 mx-auto" />
          <h3 className="text-base font-bold text-gray-900">No Reports Submitted Yet</h3>
          <p className="text-xs text-gray-500 max-w-sm mx-auto">
            You haven't reported any campus issues yet. Spot broken infrastructure? Let the institution know!
          </p>
          <div className="pt-2">
            <Link
              href="/report"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-xs font-semibold shadow-md"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Report First Issue</span>
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {issues.map((issue) => {
            const isPendingVerify = issue.status === "RESOLVED_PENDING_VERIFICATION";

            return (
              <div
                key={issue.id}
                className={`p-6 bg-white rounded-3xl border transition-all space-y-4 ${
                  isPendingVerify
                    ? "border-teal-300 ring-2 ring-teal-500/10 bg-teal-50/10 shadow-md"
                    : "border-gray-200/90 shadow-sm hover:border-gray-300"
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-bold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-full">
                        {issue.issue_type?.category} &rarr; {issue.issue_type?.sub_type}
                      </span>
                      {issue.specific_asset && (
                        <span className="text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full font-medium">
                          Asset: {issue.specific_asset}
                        </span>
                      )}
                    </div>
                    <h3 className="text-base font-bold text-gray-900">
                      {issue.title}
                    </h3>
                  </div>

                  <StatusBadge status={issue.status} />
                </div>

                <p className="text-xs text-gray-700 leading-relaxed bg-gray-50/70 p-3 rounded-2xl border border-gray-100">
                  {issue.description}
                </p>

                <div className="flex flex-wrap items-center justify-between gap-3 pt-2 text-xs text-gray-500">
                  <div className="flex flex-wrap items-center gap-4">
                    <div className="flex items-center gap-1.5 font-medium">
                      <MapPin className="w-3.5 h-3.5 text-gray-400" />
                      <span>{issue.location?.name}</span>
                    </div>

                    <div className="flex items-center gap-1.5 text-[11px] text-gray-400">
                      <Clock className="w-3.5 h-3.5" />
                      <span>Reported {new Date(issue.created_at).toLocaleDateString()}</span>
                    </div>

                    {issue.current_handler && (
                      <div className="text-[11px] text-gray-600 bg-slate-100 px-2.5 py-0.5 rounded-full">
                        Handler: <strong>{issue.current_handler.full_name}</strong>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {isPendingVerify && (
                      <button
                        type="button"
                        onClick={() => handleOpenVerify(issue)}
                        className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-xl shadow-md shadow-emerald-600/20 transition-all hover:scale-102 animate-pulse"
                      >
                        <ShieldCheck className="w-4 h-4" />
                        <span>Verify Resolution</span>
                      </button>
                    )}

                    <Link
                      href={`/issues/${issue.id}`}
                      className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-gray-700 hover:text-indigo-600 hover:bg-gray-50 rounded-xl border border-gray-200 transition-colors"
                    >
                      <span>Full Case Timeline</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Student Verify Modal */}
      <VerifyModal
        isOpen={isVerifyOpen}
        issueTitle={selectedIssueForVerify?.title || ""}
        evidence={verifyEvidence}
        onClose={() => setIsVerifyOpen(false)}
        onSubmit={handleVerifySubmit}
      />
    </div>
  );
}

