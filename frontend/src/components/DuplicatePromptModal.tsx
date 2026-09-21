"use client";

import React from "react";
import { CheckCircle2, MapPin, Users } from "lucide-react";

import { Modal } from "@/components/Modal";
import { StatusBadge } from "@/components/StatusBadge";
import { formatRelative, pluralise } from "@/lib/format";
import { DuplicateIssueCandidate } from "@/lib/types";

interface DuplicatePromptModalProps {
  open: boolean;
  candidates: DuplicateIssueCandidate[];
  submitting: boolean;
  onClose: () => void;
  onJoin: (issueId: number) => void;
  onCreateSeparate: () => void;
}

/** The suggestion is a suggestion. Nothing here merges anything automatically;
 *  the student picks, and "this is a different problem" is always available. */
export const DuplicatePromptModal: React.FC<DuplicatePromptModalProps> = ({
  open,
  candidates,
  submitting,
  onClose,
  onJoin,
  onCreateSeparate,
}) => (
  <Modal
    open={open}
    onClose={onClose}
    wide
    title="Someone may have already reported this"
    description="If one of these is the same problem, add your report to it so the handler sees how many people it affects. If not, submit yours separately."
  >
    <div className="space-y-3">
      {candidates.map((candidate) => (
        <article
          key={candidate.issue_id}
          className={`rounded-2xl border p-4 ${candidate.asset_match ? "border-indigo-200 bg-indigo-50/40" : "border-gray-200"}`}
        >
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-sm font-semibold text-gray-900">{candidate.title}</p>
              <p className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-gray-500">
                <span className="inline-flex items-center gap-1">
                  <MapPin className="h-3 w-3" aria-hidden />
                  {candidate.location_name}
                </span>
                <span className="inline-flex items-center gap-1">
                  <Users className="h-3 w-3" aria-hidden />
                  {pluralise(candidate.affected_student_count, "student")} affected
                </span>
                <span>Reported {formatRelative(candidate.created_at)}</span>
              </p>
            </div>
            <StatusBadge status={candidate.status} />
          </div>

          <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-gray-600">{candidate.description}</p>

          {candidate.specific_asset ? (
            <p className="mt-2 text-[11px] text-gray-500">
              Reported against <span className="font-semibold">{candidate.specific_asset}</span>
              {candidate.asset_match ? null : " — which is not the item you selected."}
            </p>
          ) : null}

          <div className="mt-3">
            {candidate.already_reported_by_you ? (
              <p className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-3 py-1.5 text-[11px] font-semibold text-gray-600">
                <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
                You have already reported this one
              </p>
            ) : (
              <button
                type="button"
                disabled={submitting}
                onClick={() => onJoin(candidate.issue_id)}
                className="rounded-full bg-indigo-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                This is the same problem
              </button>
            )}
          </div>
        </article>
      ))}

      <div className="flex flex-col gap-2 border-t border-gray-100 pt-4 sm:flex-row sm:justify-end">
        <button type="button" onClick={onClose} className="rounded-full px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">
          Go back
        </button>
        <button
          type="button"
          disabled={submitting}
          onClick={onCreateSeparate}
          className="rounded-full border border-gray-300 px-5 py-2 text-sm font-semibold text-gray-800 hover:bg-gray-50 disabled:opacity-50"
        >
          {submitting ? "Submitting…" : "None of these — submit mine separately"}
        </button>
      </div>
    </div>
  </Modal>
);
