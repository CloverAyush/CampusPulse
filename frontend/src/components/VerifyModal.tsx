"use client";

import React, { useState } from "react";
import { CheckCircle2, ExternalLink, ThumbsDown } from "lucide-react";

import { InlineError } from "@/components/States";
import { Modal } from "@/components/Modal";
import { errorMessage } from "@/lib/api";
import { formatDateTime, safeExternalUrl } from "@/lib/format";
import { Issue, ResolutionEvidence, VerificationStatus } from "@/lib/types";

interface VerifyModalProps {
  open: boolean;
  issue: Issue | null;
  evidence: ResolutionEvidence | null;
  onClose: () => void;
  onSubmit: (data: { status: VerificationStatus; comment?: string }) => Promise<void>;
}

export const VerifyModal: React.FC<VerifyModalProps> = ({ open, issue, evidence, onClose, onSubmit }) => {
  const [choice, setChoice] = useState<VerificationStatus | null>(null);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!issue) return null;

  const evidenceLink = safeExternalUrl(evidence?.attachment_url);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!choice) {
      setError("Let us know whether it is fixed.");
      return;
    }
    if (choice === "disputed" && comment.trim().length === 0) {
      setError("Tell the handler what is still wrong so they know what to look at.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({ status: choice, comment: comment.trim() || undefined });
      setChoice(null);
      setComment("");
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Is this actually fixed?"
      description="Your answer settles it. Confirming closes the issue; disputing sends it straight back to the handler."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="rounded-xl bg-gray-50 px-3 py-2 text-xs text-gray-600">{issue.title}</p>

        {evidence ? (
          <section className="rounded-2xl border border-teal-200 bg-teal-50 p-3">
            <p className="text-[11px] font-bold uppercase tracking-wider text-teal-700">What the handler reported</p>
            <p className="mt-1 whitespace-pre-line text-xs leading-relaxed text-teal-900">{evidence.notes}</p>
            <p className="mt-1.5 text-[10px] text-teal-600">
              {evidence.submitted_by?.full_name ?? "Handler"} · {formatDateTime(evidence.created_at)}
            </p>
            {evidenceLink ? (
              <a
                href={evidenceLink}
                target="_blank"
                rel="noopener noreferrer nofollow"
                className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-teal-700 hover:underline"
              >
                View the evidence
                <ExternalLink className="h-3 w-3" aria-hidden />
              </a>
            ) : null}
          </section>
        ) : (
          <p className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
            No evidence was attached to this resolution.
          </p>
        )}

        <fieldset className="grid gap-2 sm:grid-cols-2">
          <legend className="sr-only">Is it fixed?</legend>
          <label
            className={`flex cursor-pointer items-center gap-2 rounded-xl border px-3 py-2.5 text-sm font-semibold transition ${
              choice === "confirmed" ? "border-emerald-400 bg-emerald-50 text-emerald-900" : "border-gray-200 hover:border-gray-300"
            }`}
          >
            <input type="radio" name="verification" checked={choice === "confirmed"} onChange={() => setChoice("confirmed")} className="sr-only" />
            <CheckCircle2 className="h-4 w-4 text-emerald-600" aria-hidden />
            Yes, it is fixed
          </label>
          <label
            className={`flex cursor-pointer items-center gap-2 rounded-xl border px-3 py-2.5 text-sm font-semibold transition ${
              choice === "disputed" ? "border-rose-400 bg-rose-50 text-rose-900" : "border-gray-200 hover:border-gray-300"
            }`}
          >
            <input type="radio" name="verification" checked={choice === "disputed"} onChange={() => setChoice("disputed")} className="sr-only" />
            <ThumbsDown className="h-4 w-4 text-rose-600" aria-hidden />
            No, still a problem
          </label>
        </fieldset>

        <div>
          <label htmlFor="verify-comment" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
            Comment {choice === "disputed" ? "" : <span className="font-medium normal-case text-gray-400">(optional)</span>}
          </label>
          <textarea
            id="verify-comment"
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            rows={3}
            maxLength={1000}
            placeholder={choice === "disputed" ? "The fan runs but still makes the same grinding noise." : "Working normally again."}
            className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
        </div>

        <InlineError message={error} />

        <div className="flex justify-end gap-2 pt-1">
          <button type="button" onClick={onClose} className="rounded-full px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">
            Not now
          </button>
          <button
            type="submit"
            disabled={submitting || !choice}
            className="rounded-full bg-indigo-600 px-5 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Sending…" : "Submit"}
          </button>
        </div>
      </form>
    </Modal>
  );
};
