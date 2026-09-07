"use client";

import React, { useState } from "react";
import { VerificationStatus, ResolutionEvidence } from "@/lib/types";
import { CheckCircle, XCircle, X, ShieldCheck, ExternalLink, FileText } from "lucide-react";

interface VerifyModalProps {
  isOpen: boolean;
  issueTitle: string;
  evidence?: ResolutionEvidence | null;
  onClose: () => void;
  onSubmit: (data: { status: VerificationStatus; comment?: string }) => Promise<void>;
}

export const VerifyModal: React.FC<VerifyModalProps> = ({
  isOpen,
  issueTitle,
  evidence,
  onClose,
  onSubmit,
}) => {
  const [status, setStatus] = useState<VerificationStatus>("confirmed");
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await onSubmit({
        status,
        comment: comment.trim() || undefined,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to submit verification");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full overflow-hidden border border-gray-100 flex flex-col">
        {/* Header */}
        <div className="bg-emerald-50 px-6 py-5 border-b border-emerald-100 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-600 text-white rounded-2xl shadow-md shadow-emerald-600/20">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-gray-900">Verify Issue Resolution</h3>
              <p className="text-xs text-emerald-800 line-clamp-1">{issueTitle}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 text-xs bg-rose-50 text-rose-700 border border-rose-200 rounded-xl font-medium">
              {error}
            </div>
          )}

          {/* Evidence Details Preview */}
          {evidence && (
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200/80 space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                <span className="flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-slate-500" />
                  Handler Proof Submitted ({evidence.evidence_type.replace("_", " ")})
                </span>
                {evidence.submitted_by && (
                  <span className="text-[11px] font-normal text-slate-500">
                    by {evidence.submitted_by.full_name}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-800 bg-white p-2.5 rounded-xl border border-slate-200/60 leading-relaxed">
                {evidence.notes}
              </p>
              {evidence.attachment_url && (
                <a
                  href={evidence.attachment_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-indigo-600 hover:text-indigo-800 font-semibold mt-1"
                >
                  <span>View Attached Photo / Document Proof</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          )}

          {/* Verification Choice */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-2">
              Did this resolution fix the problem?
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setStatus("confirmed")}
                className={`flex flex-col items-center justify-center p-4 rounded-2xl border-2 transition-all text-center gap-2 ${
                  status === "confirmed"
                    ? "border-emerald-500 bg-emerald-50/60 text-emerald-950 shadow-sm"
                    : "border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
                }`}
              >
                <CheckCircle
                  className={`w-6 h-6 ${
                    status === "confirmed" ? "text-emerald-600" : "text-gray-400"
                  }`}
                />
                <div>
                  <div className="text-xs font-bold">Yes, Confirmed Fixed</div>
                  <div className="text-[10px] text-gray-500 mt-0.5">Closes the issue</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setStatus("disputed")}
                className={`flex flex-col items-center justify-center p-4 rounded-2xl border-2 transition-all text-center gap-2 ${
                  status === "disputed"
                    ? "border-rose-500 bg-rose-50/60 text-rose-950 shadow-sm"
                    : "border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
                }`}
              >
                <XCircle
                  className={`w-6 h-6 ${
                    status === "disputed" ? "text-rose-600" : "text-gray-400"
                  }`}
                />
                <div>
                  <div className="text-xs font-bold">No, Still Broken</div>
                  <div className="text-[10px] text-gray-500 mt-0.5">Reopens issue</div>
                </div>
              </button>
            </div>
          </div>

          {/* Student Comment */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Feedback Remarks <span className="text-gray-400 font-normal">({status === "disputed" ? "Explain what is still broken" : "Optional"})</span>
            </label>
            <textarea
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={
                status === "confirmed"
                  ? "E.g., Fan is running smoothly now, thanks!"
                  : "E.g., Fan started spinning but still makes high-pitched clicking noise..."
              }
              className="w-full text-xs p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
          </div>

          {/* Footer Actions */}
          <div className="pt-3 flex items-center justify-end gap-2 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-gray-600 hover:bg-gray-100 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className={`px-5 py-2.5 text-xs font-semibold text-white rounded-xl shadow-md transition-all disabled:opacity-50 ${
                status === "confirmed"
                  ? "bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/20"
                  : "bg-rose-600 hover:bg-rose-700 shadow-rose-600/20"
              }`}
            >
              {loading
                ? "Submitting..."
                : status === "confirmed"
                ? "Confirm & Close Issue"
                : "Dispute & Reopen Issue"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

