"use client";

import React, { useState } from "react";

import { InlineError } from "@/components/States";
import { Modal } from "@/components/Modal";
import { errorMessage } from "@/lib/api";
import { EvidenceType, Issue } from "@/lib/types";

const EVIDENCE_OPTIONS: { value: EvidenceType; label: string; hint: string }[] = [
  { value: "photo", label: "Photo", hint: "A link to a photo of the completed work" },
  { value: "description", label: "Action description", hint: "What you did, in your own words" },
  { value: "maintenance_record", label: "Maintenance record", hint: "Job card, work order or invoice" },
  { value: "screenshot", label: "Screenshot", hint: "For network or system fixes" },
  { value: "other", label: "Other", hint: "Anything else that proves the work" },
];

const MIN_NOTES = 10;

interface ResolveModalProps {
  open: boolean;
  issue: Issue | null;
  onClose: () => void;
  onSubmit: (data: { evidence_type: EvidenceType; notes: string; attachment_url?: string }) => Promise<void>;
}

export const ResolveModal: React.FC<ResolveModalProps> = ({ open, issue, onClose, onSubmit }) => {
  const [evidenceType, setEvidenceType] = useState<EvidenceType>("description");
  const [notes, setNotes] = useState("");
  const [attachmentUrl, setAttachmentUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!issue) return null;

  const notesTooShort = notes.trim().length < MIN_NOTES;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (notesTooShort) {
      setError(`Describe what you did in at least ${MIN_NOTES} characters.`);
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({
        evidence_type: evidenceType,
        notes: notes.trim(),
        attachment_url: attachmentUrl.trim() || undefined,
      });
      setNotes("");
      setAttachmentUrl("");
      setEvidenceType("description");
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
      title="Mark as resolved"
      description={
        issue.requires_verification
          ? "The students who reported this will be asked to confirm it is actually fixed."
          : "This issue type closes immediately once you record the work."
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="rounded-xl bg-gray-50 px-3 py-2 text-xs text-gray-600">{issue.title}</p>

        <fieldset>
          <legend className="mb-1.5 text-xs font-bold uppercase tracking-wider text-gray-500">
            Evidence type
          </legend>
          <div className="grid gap-1.5 sm:grid-cols-2">
            {EVIDENCE_OPTIONS.map((option) => (
              <label
                key={option.value}
                className={`cursor-pointer rounded-xl border px-3 py-2 text-xs transition ${
                  evidenceType === option.value
                    ? "border-indigo-400 bg-indigo-50 text-indigo-900"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <input
                  type="radio"
                  name="evidence_type"
                  value={option.value}
                  checked={evidenceType === option.value}
                  onChange={() => setEvidenceType(option.value)}
                  className="sr-only"
                />
                <span className="block font-semibold">{option.label}</span>
                <span className="mt-0.5 block text-[11px] text-gray-500">{option.hint}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <div>
          <label htmlFor="resolve-notes" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
            What did you do?
          </label>
          <textarea
            id="resolve-notes"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            rows={4}
            maxLength={2000}
            required
            placeholder="Replaced the fan regulator and tested it on all three speeds."
            className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <p className="mt-1 text-[11px] text-gray-400">
            {notes.trim().length}/2000 characters. Minimum {MIN_NOTES}.
          </p>
        </div>

        <div>
          <label htmlFor="resolve-url" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
            Evidence link <span className="font-medium normal-case text-gray-400">(optional)</span>
          </label>
          <input
            id="resolve-url"
            type="url"
            inputMode="url"
            value={attachmentUrl}
            onChange={(event) => setAttachmentUrl(event.target.value)}
            placeholder="https://drive.example.edu/work-order-4821.jpg"
            className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <p className="mt-1 text-[11px] text-gray-400">Must be an https link.</p>
        </div>

        <InlineError message={error} />

        <div className="flex justify-end gap-2 pt-1">
          <button type="button" onClick={onClose} className="rounded-full px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting || notesTooShort}
            className="rounded-full bg-teal-600 px-5 py-2 text-sm font-semibold text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Saving…" : "Mark resolved"}
          </button>
        </div>
      </form>
    </Modal>
  );
};
