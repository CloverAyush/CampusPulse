"use client";

import React, { useEffect, useState } from "react";

import { InlineError } from "@/components/States";
import { Modal } from "@/components/Modal";
import { api, errorMessage } from "@/lib/api";
import { Issue, UserPublic } from "@/lib/types";

const MIN_REASON = 15;

interface EscalateModalProps {
  open: boolean;
  issue: Issue | null;
  onClose: () => void;
  onSubmit: (data: { reason: string; escalated_to_id?: number }) => Promise<void>;
}

export const EscalateModal: React.FC<EscalateModalProps> = ({ open, issue, onClose, onSubmit }) => {
  const [reason, setReason] = useState("");
  const [targetId, setTargetId] = useState<string>("");
  const [targets, setTargets] = useState<UserPublic[]>([]);
  const [targetsError, setTargetsError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !issue) return;

    let cancelled = false;

    api
      .getEscalationTargets(issue.id)
      .then((result) => {
        if (cancelled) return;
        setTargets(result);
        setTargetsError(null);
      })
      .catch((cause) => {
        if (!cancelled) setTargetsError(errorMessage(cause));
      });

    return () => {
      cancelled = true;
    };
  }, [open, issue]);

  if (!issue) return null;

  const reasonTooShort = reason.trim().length < MIN_REASON;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (reasonTooShort) {
      setError(`State why this is outside your authority in at least ${MIN_REASON} characters.`);
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({
        reason: reason.trim(),
        escalated_to_id: targetId ? Number(targetId) : undefined,
      });
      setReason("");
      setTargetId("");
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
      title="Escalate this issue"
      description="The authority receives the full case: every report, all evidence and the complete history. Nothing is summarised away."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="rounded-xl bg-gray-50 px-3 py-2 text-xs text-gray-600">{issue.title}</p>

        <div>
          <label htmlFor="escalate-reason" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
            Why is this beyond your authority?
          </label>
          <textarea
            id="escalate-reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            rows={4}
            maxLength={2000}
            required
            placeholder="Rewiring the second-floor circuit needs a budget sanction and an external contractor."
            className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <p className="mt-1 text-[11px] text-gray-400">Minimum {MIN_REASON} characters.</p>
        </div>

        <div>
          <label htmlFor="escalate-target" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
            Escalate to
          </label>
          <select
            id="escalate-target"
            value={targetId}
            onChange={(event) => setTargetId(event.target.value)}
            className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          >
            <option value="">First available authority</option>
            {targets.map((target) => (
              <option key={target.id} value={target.id}>
                {target.full_name}
              </option>
            ))}
          </select>
          {targetsError ? (
            <p className="mt-1 text-[11px] text-amber-700">
              Could not load the authority list ({targetsError}). Leaving this on the default still works.
            </p>
          ) : null}
        </div>

        <InlineError message={error} />

        <div className="flex justify-end gap-2 pt-1">
          <button type="button" onClick={onClose} className="rounded-full px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting || reasonTooShort}
            className="rounded-full bg-purple-600 px-5 py-2 text-sm font-semibold text-white hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Escalating…" : "Escalate"}
          </button>
        </div>
      </form>
    </Modal>
  );
};
