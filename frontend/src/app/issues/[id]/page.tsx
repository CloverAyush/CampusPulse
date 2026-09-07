"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { IssueDetail, EvidenceType, VerificationStatus } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";
import { IssueTimeline } from "@/components/IssueTimeline";
import { ResolveModal } from "@/components/ResolveModal";
import { EscalateModal } from "@/components/EscalateModal";
import { VerifyModal } from "@/components/VerifyModal";
import {
  ArrowLeft,
  MapPin,
  Clock,
  Users,
  ShieldCheck,
  Wrench,
  AlertOctagon,
  CheckCircle2,
  ExternalLink,
  Tag,
  Building,
  FileCheck,
} from "lucide-react";

export default function IssueDetailPage() {
  const params = useParams();
  const router = useRouter();
  const issueId = Number(params?.id);
  const { user } = useAuth();

  const [issue, setIssue] = useState<IssueDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [isResolveOpen, setIsResolveOpen] = useState(false);
  const [isEscalateOpen, setIsEscalateOpen] = useState(false);
  const [isVerifyOpen, setIsVerifyOpen] = useState(false);
  const [authorities, setAuthorities] = useState([]);

  const loadIssue = async () => {
    if (!issueId) return;
    setLoading(true);
    try {
      const data = await api.getIssue(issueId);
      setIssue(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load issue");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && issueId) {
      loadIssue();
      api.listUsers("higher_authority").then((auths: any) => setAuthorities(auths)).catch(() => {});
    }
  }, [user, issueId]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-12 text-center">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-xs text-gray-500 font-medium">Loading issue details & full timeline...</p>
      </div>
    );
  }

  if (error || !issue) {
    return (
      <div className="max-w-xl mx-auto p-12 text-center bg-white rounded-3xl border border-gray-200">
        <h3 className="text-base font-bold text-gray-900 mb-2">Issue Not Found</h3>
        <p className="text-xs text-gray-500 mb-4">{error || "The requested issue does not exist."}</p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Home</span>
        </Link>
      </div>
    );
  }

  const isHandler = user && issue.current_handler_id === user.id;
  const isAuthorityOrAdmin = user && (user.role === "higher_authority" || user.role === "admin");
  const isReporter = user && issue.reports.some((r) => r.reporter_id === user.id);

  const canResolve = (isHandler || isAuthorityOrAdmin) && issue.status !== "VERIFIED_CLOSED";
  const canEscalate = isHandler && issue.status !== "ESCALATED" && issue.status !== "VERIFIED_CLOSED";
  const canVerify = (isReporter || user?.role === "admin") && issue.status === "RESOLVED_PENDING_VERIFICATION";

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Top Breadcrumb & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <button
          type="button"
          onClick={() => router.back()}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to previous page</span>
        </button>

        <div className="flex flex-wrap items-center gap-2">
          {canVerify && (
            <button
              onClick={() => setIsVerifyOpen(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-xl shadow-md shadow-emerald-600/20 transition-all animate-pulse"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Verify Resolution</span>
            </button>
          )}

          {canResolve && (
            <button
              onClick={() => setIsResolveOpen(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs rounded-xl shadow-md shadow-teal-600/20 transition-all"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Resolve with Evidence</span>
            </button>
          )}

          {canEscalate && (
            <button
              onClick={() => setIsEscalateOpen(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 font-semibold text-xs rounded-xl transition-all"
            >
              <AlertOctagon className="w-4 h-4" />
              <span>Escalate to Authority</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Issue Header Card */}
      <div className="bg-white rounded-3xl border border-gray-200/90 shadow-sm p-6 sm:p-8 space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-indigo-700 bg-indigo-50 px-3 py-1 rounded-full">
                {issue.issue_type?.category} &rarr; {issue.issue_type?.sub_type}
              </span>
              {issue.specific_asset && (
                <span className="text-xs text-gray-700 bg-gray-100 px-2.5 py-1 rounded-full font-semibold">
                  Asset: {issue.specific_asset}
                </span>
              )}
              <span className="text-xs text-gray-500 bg-gray-100 px-2.5 py-1 rounded-full">
                {issue.requires_verification ? "Verification Required" : "Direct Closure"}
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
              {issue.title}
            </h1>
          </div>

          <StatusBadge status={issue.status} size="lg" />
        </div>

        <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
          <div className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
            Institutional Problem Summary
          </div>
          <p className="text-xs text-gray-800 leading-relaxed whitespace-pre-line">
            {issue.description}
          </p>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-gray-100 text-xs">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gray-100 text-gray-600">
              <MapPin className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[11px] text-gray-400 font-medium">Location</div>
              <div className="font-semibold text-gray-900">{issue.location?.name}</div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gray-100 text-gray-600">
              <Wrench className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[11px] text-gray-400 font-medium">Assigned Handler</div>
              <div className="font-semibold text-gray-900">
                {issue.current_handler?.full_name || "Unassigned"}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gray-100 text-gray-600">
              <Users className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[11px] text-gray-400 font-medium">Student Impact Signal</div>
              <div className="font-semibold text-gray-900">
                {issue.report_count} {issue.report_count === 1 ? "student report" : "student reports"} linked
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Linked Student Reports Section */}
      <div className="bg-white rounded-3xl border border-gray-200/90 shadow-sm p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-gray-100">
          <div>
            <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
              <Users className="w-4 h-4 text-indigo-600" />
              <span>Linked Student Submissions ({issue.reports.length})</span>
            </h2>
            <p className="text-xs text-gray-500">
              All independent student reports matched to this underlying institutional problem.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {issue.reports.map((report, idx) => (
            <div
              key={report.id}
              className="p-4 rounded-2xl border border-gray-200 bg-gray-50/50 space-y-2 text-xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-gray-900">
                  Report #{idx + 1} — {report.reporter?.full_name || "Student"}
                </span>
                <span className="text-[10px] text-gray-400">
                  {new Date(report.created_at).toLocaleDateString()}
                </span>
              </div>
              <p className="text-gray-700 bg-white p-2.5 rounded-xl border border-gray-100 leading-relaxed">
                "{report.description}"
              </p>
              {report.photo_url && (
                <a
                  href={report.photo_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-indigo-600 font-medium text-[11px] hover:underline"
                >
                  <span>View Attached Photo</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Complete Audit Timeline */}
      <div className="bg-white rounded-3xl border border-gray-200/90 shadow-sm p-6 sm:p-8 space-y-6">
        <div className="pb-3 border-b border-gray-100">
          <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-indigo-600" />
            <span>Complete Case History & Timeline</span>
          </h2>
          <p className="text-xs text-gray-500">
            Immutable chronological audit log of all deterministic routing, actions, escalations, proof, and verifications.
          </p>
        </div>

        <IssueTimeline events={issue.timeline_events} />
      </div>

      {/* Modals */}
      <ResolveModal
        isOpen={isResolveOpen}
        issueTitle={issue.title}
        requiresVerification={issue.requires_verification}
        onClose={() => setIsResolveOpen(false)}
        onSubmit={async (data) => {
          await api.resolveIssue(issue.id, data);
          loadIssue();
        }}
      />

      <EscalateModal
        isOpen={isEscalateOpen}
        issueTitle={issue.title}
        authorities={authorities}
        onClose={() => setIsEscalateOpen(false)}
        onSubmit={async (data) => {
          await api.escalateIssue(issue.id, data);
          loadIssue();
        }}
      />

      <VerifyModal
        isOpen={isVerifyOpen}
        issueTitle={issue.title}
        evidence={issue.evidences.length > 0 ? issue.evidences[0] : null}
        onClose={() => setIsVerifyOpen(false)}
        onSubmit={async (data) => {
          await api.verifyIssue(issue.id, data);
          loadIssue();
        }}
      />
    </div>
  );
}

