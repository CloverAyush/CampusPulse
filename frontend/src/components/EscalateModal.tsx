"use client";

import React, { useState } from "react";
import { User } from "@/lib/types";
import { AlertOctagon, X, ShieldAlert, ArrowUpRight } from "lucide-react";

interface EscalateModalProps {
  isOpen: boolean;
  issueTitle: string;
  authorities: User[];
  onClose: () => void;
  onSubmit: (data: { reason: string; escalated_to_id?: number }) => Promise<void>;
}

export const EscalateModal: React.FC<EscalateModalProps> = ({
  isOpen,
  issueTitle,
  authorities,
  onClose,
  onSubmit,
}) => {
  const [reason, setReason] = useState("");
  const [targetId, setTargetId] = useState<number | undefined>(
    authorities.length > 0 ? authorities[0].id : undefined
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) {
      setError("Please state the specific reason for escalating this issue to higher authority.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await onSubmit({
        reason: reason.trim(),
        escalated_to_id: targetId,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to escalate issue");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full overflow-hidden border border-gray-100 flex flex-col">
        {/* Header */}
        <div className="bg-purple-50 px-6 py-5 border-b border-purple-100 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-purple-600 text-white rounded-2xl shadow-md shadow-purple-600/20">
              <AlertOctagon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-gray-900">Escalate to Higher Authority</h3>
              <p className="text-xs text-purple-800 line-clamp-1">{issueTitle}</p>
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

          <div className="bg-purple-50/50 p-3.5 rounded-xl border border-purple-100 text-xs text-purple-950 flex items-start gap-2.5 leading-relaxed">
            <ShieldAlert className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
            <span>
              <strong>Deterministic Case Preservation:</strong> The entire case history, original student
              reports, previous actions, and your stated reason will be forwarded directly to the higher
              authority with zero summarization.
            </span>
          </div>

          {/* Target Higher Authority */}
          {authorities.length > 0 && (
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Forward To Authority
              </label>
              <select
                value={targetId || ""}
                onChange={(e) => setTargetId(Number(e.target.value))}
                className="w-full text-xs px-3 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none bg-white"
              >
                {authorities.map((auth) => (
                  <option key={auth.id} value={auth.id}>
                    {auth.full_name} ({auth.department || "Deanery / Authority"})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Escalation Reason */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Stated Reason for Escalation <span className="text-rose-500">*</span>
            </label>
            <textarea
              required
              rows={4}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="State why this cannot be resolved at your tier (e.g. requires budget sanction > 10,000 INR, external vendor contract approval, or major structural civil work)..."
              className="w-full text-xs p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
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
              className="inline-flex items-center gap-1.5 px-5 py-2.5 text-xs font-semibold text-white bg-purple-600 hover:bg-purple-700 rounded-xl shadow-md shadow-purple-600/20 transition-all disabled:opacity-50"
            >
              <span>{loading ? "Escalating..." : "Confirm Escalation"}</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

