"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, ExternalLink, MapPin, Paperclip, Users } from "lucide-react";

import { EscalateModal } from "@/components/EscalateModal";
import { IssueTimeline } from "@/components/IssueTimeline";
import { ResolveModal } from "@/components/ResolveModal";
import { StatusBadge } from "@/components/StatusBadge";
import { ErrorState, InlineError, LoadingState } from "@/components/States";
import { VerifyModal } from "@/components/VerifyModal";
import { api, errorMessage } from "@/lib/api";
import { hasRole, useAuth } from "@/lib/auth";
import { formatDateTime, formatRelative, pluralise, safeExternalUrl } from "@/lib/format";
import { EvidenceType, IssueDetail, VerificationStatus } from "@/lib/types";

export default function IssueDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const issueId = Number(params?.id);

  const [issue, setIssue] = useState<IssueDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [resolveOpen, setResolveOpen] = useState(false);
  const [escalateOpen, setEscalateOpen] = useState(false);
  const [verifyOpen, setVerifyOpen] = useState(false);

  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        if (!Number.isFinite(issueId)) {
          throw new Error("That issue reference is not valid.");
        }
        const detail = await api.getIssue(issueId);
        if (cancelled) return;
        setIssue(detail);
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
  }, [issueId, reloadToken]);

  const reload = useCallback(() => {
    setLoading(true);
    setReloadToken((token) => token + 1);
  }, []);

  const refresh = useCallback(() => setReloadToken((token) => token + 1), []);

  if (loading) return <LoadingState label="Loading issue" />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!issue) return null;

  const isAssignedHandler = issue.current_handler_id === user?.id;
  const canWorkOnIt =
    isAssignedHandler || hasRole(user, "admin", "higher_authority");
  const isOpenForWork = ["OPEN", "IN_PROGRESS", "REOPENED", "ESCALATED"].includes(issue.status);
  const latestEvidence = issue.evidences[0] ?? null;

  const runAction = async (action: () => Promise<unknown>) => {
    setBusy(true);
    setActionError(null);
    try {
      await action();
      refresh();
    } catch (cause) {
      setActionError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  };

  const handleResolve = async (data: { evidence_type: EvidenceType; notes: string; attachment_url?: string }) => {
    await api.resolveIssue(issue.id, data);
    setResolveOpen(false);
    refresh();
  };

  const handleEscalate = async (data: { reason: string; escalated_to_id?: number }) => {
    await api.escalateIssue(issue.id, data);
    setEscalateOpen(false);
    refresh();
  };

  const handleVerify = async (data: { status: VerificationStatus; comment?: string }) => {
    await api.verifyIssue(issue.id, data);
    setVerifyOpen(false);
    refresh();
  };

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <button
        type="button"
        onClick={() => router.back()}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-gray-900"
      >
        <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
        Back
      </button>

      <header className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-xl font-bold tracking-tight">{issue.title}</h1>
            <p className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
              <span className="inline-flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" aria-hidden />
                {issue.location?.name ?? "Unknown location"}
              </span>
              <span className="inline-flex items-center gap-1">
                <Users className="h-3.5 w-3.5" aria-hidden />
                {pluralise(issue.affected_student_count, "student")} affected
              </span>
              <span>Reported {formatRelative(issue.created_at)}</span>
            </p>
          </div>
          <StatusBadge status={issue.status} />
        </div>

        <p className="mt-4 whitespace-pre-line text-sm leading-relaxed text-gray-700">{issue.description}</p>

        <dl className="mt-5 grid gap-3 border-t border-gray-100 pt-4 text-xs sm:grid-cols-3">
          <div>
            <dt className="font-bold uppercase tracking-wider text-gray-400">Category</dt>
            <dd className="mt-0.5 text-gray-800">
              {issue.issue_type ? `${issue.issue_type.category} · ${issue.issue_type.sub_type}` : "Uncategorised"}
            </dd>
          </div>
          <div>
            <dt className="font-bold uppercase tracking-wider text-gray-400">Assigned to</dt>
            <dd className="mt-0.5 text-gray-800">{issue.current_handler?.full_name ?? "Awaiting triage"}</dd>
          </div>
          <div>
            <dt className="font-bold uppercase tracking-wider text-gray-400">Specific item</dt>
            <dd className="mt-0.5 text-gray-800">{issue.specific_asset ?? "Not specified"}</dd>
          </div>
        </dl>

        <InlineError message={actionError} />

        <div className="mt-4 flex flex-wrap gap-2">
          {canWorkOnIt && isOpenForWork ? (
            <>
              {["OPEN", "REOPENED"].includes(issue.status) ? (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void runAction(() => api.startProgress(issue.id))}
                  className="rounded-full bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  Start work
                </button>
              ) : null}
              <button
                type="button"
                onClick={() => setResolveOpen(true)}
                className="rounded-full bg-teal-600 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-700"
              >
                Mark resolved
              </button>
              {issue.status !== "ESCALATED" ? (
                <button
                  type="button"
                  onClick={() => setEscalateOpen(true)}
                  className="rounded-full border border-purple-300 px-4 py-2 text-xs font-semibold text-purple-700 hover:bg-purple-50"
                >
                  Escalate
                </button>
              ) : null}
            </>
          ) : null}

          {issue.viewer_can_verify ? (
            <button
              type="button"
              onClick={() => setVerifyOpen(true)}
              className="rounded-full bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700"
            >
              Confirm whether this is fixed
            </button>
          ) : null}
        </div>
      </header>

      {issue.evidences.length > 0 ? (
        <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-gray-500">Resolution evidence</h2>
          <ul className="space-y-3">
            {issue.evidences.map((evidence) => {
              const link = safeExternalUrl(evidence.attachment_url);
              return (
                <li key={evidence.id} className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                      {evidence.evidence_type.replace("_", " ")} · attempt {evidence.resolution_round}
                    </p>
                    <time dateTime={evidence.created_at} className="text-[11px] text-gray-400">
                      {formatDateTime(evidence.created_at)}
                    </time>
                  </div>
                  <p className="mt-1.5 whitespace-pre-line text-sm leading-relaxed text-gray-700">{evidence.notes}</p>
                  <p className="mt-1.5 text-[11px] text-gray-500">
                    Submitted by {evidence.submitted_by?.full_name ?? "a staff member"}
                  </p>
                  {link ? (
                    <a
                      href={link}
                      target="_blank"
                      rel="noopener noreferrer nofollow"
                      className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:underline"
                    >
                      Open the attached evidence
                      <ExternalLink className="h-3 w-3" aria-hidden />
                    </a>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}

      <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-gray-500">
          Reports ({issue.reports.length})
        </h2>
        <ul className="space-y-3">
          {issue.reports.map((report) => {
            const photo = safeExternalUrl(report.photo_url);
            return (
              <li key={report.id} className="rounded-2xl border border-gray-100 p-4">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="text-xs font-semibold text-gray-800">
                    {report.reporter?.full_name ?? "A student"}
                  </p>
                  <time dateTime={report.created_at} className="text-[11px] text-gray-400">
                    {formatDateTime(report.created_at)}
                  </time>
                </div>
                <p className="mt-1.5 whitespace-pre-line text-sm leading-relaxed text-gray-700">{report.description}</p>
                {report.reporter_contact ? (
                  <p className="mt-1.5 text-[11px] text-gray-500">
                    Contact: {report.reporter_contact.email}
                    {report.reporter_contact.phone ? ` · ${report.reporter_contact.phone}` : ""}
                  </p>
                ) : null}
                {photo ? (
                  <a
                    href={photo}
                    target="_blank"
                    rel="noopener noreferrer nofollow"
                    className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:underline"
                  >
                    <Paperclip className="h-3 w-3" aria-hidden />
                    View the attached photo
                  </a>
                ) : null}
              </li>
            );
          })}
        </ul>
      </section>

      {issue.escalations.length > 0 ? (
        <section className="rounded-3xl border border-purple-200 bg-purple-50/50 p-6">
          <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-purple-700">Escalations</h2>
          <ul className="space-y-3">
            {issue.escalations.map((escalation) => (
              <li key={escalation.id} className="rounded-2xl border border-purple-100 bg-white p-4">
                <p className="text-xs font-semibold text-gray-800">
                  {escalation.escalated_by?.full_name ?? "A handler"} → {escalation.escalated_to?.full_name ?? "an authority"}
                </p>
                <p className="mt-1.5 whitespace-pre-line text-sm leading-relaxed text-gray-700">{escalation.reason}</p>
                <time dateTime={escalation.created_at} className="mt-1.5 block text-[11px] text-gray-400">
                  {formatDateTime(escalation.created_at)}
                </time>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-sm font-bold uppercase tracking-wider text-gray-500">History</h2>
        <IssueTimeline events={issue.timeline_events} />
      </section>

      <p className="pb-4 text-center text-[11px] text-gray-400">
        <Link href="/my-reports" className="hover:underline">
          Back to all issues
        </Link>
      </p>

      <ResolveModal open={resolveOpen} issue={issue} onClose={() => setResolveOpen(false)} onSubmit={handleResolve} />
      <EscalateModal open={escalateOpen} issue={issue} onClose={() => setEscalateOpen(false)} onSubmit={handleEscalate} />
      <VerifyModal
        open={verifyOpen}
        issue={issue}
        evidence={latestEvidence}
        onClose={() => setVerifyOpen(false)}
        onSubmit={handleVerify}
      />
    </div>
  );
}
