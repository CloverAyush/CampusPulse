"use client";

import React, { useState } from "react";
import { EvidenceType } from "@/lib/types";
import { CheckCircle2, FileCheck, X, Link as LinkIcon, Camera, FileText } from "lucide-react";

interface ResolveModalProps {
  isOpen: boolean;
  issueTitle: string;
  requiresVerification: boolean;
  onClose: () => void;
  onSubmit: (data: { evidence_type: EvidenceType; notes: string; attachment_url?: string }) => Promise<void>;
}

export const ResolveModal: React.FC<ResolveModalProps> = ({
  isOpen,
  issueTitle,
  requiresVerification,
  onClose,
  onSubmit,
}) => {
  const [evidenceType, setEvidenceType] = useState<EvidenceType>("photo");
  const [notes, setNotes] = useState("");
  const [attachmentUrl, setAttachmentUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notes.trim()) {
      setError("Please describe the actions taken to resolve the issue.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await onSubmit({
        evidence_type: evidenceType,
        notes: notes.trim(),
        attachment_url: attachmentUrl.trim() || undefined,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to resolve issue");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full overflow-hidden border border-gray-100 flex flex-col">
        {/* Header */}
        <div className="bg-teal-50 px-6 py-5 border-b border-teal-100 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-teal-600 text-white rounded-2xl shadow-md shadow-teal-600/20">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-gray-900">Resolve Issue with Evidence</h3>
              <p className="text-xs text-teal-800 line-clamp-1">{issueTitle}</p>
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

          <div className="bg-teal-50/50 p-3 rounded-xl border border-teal-100 text-xs text-teal-900 leading-relaxed">
            <span className="font-bold">Verification Policy: </span>
            {requiresVerification
              ? "This issue requires Student Verification. Affected student(s) will be notified to confirm or dispute your resolution."
              : "Direct Closure: This issue type does not require student verification and will close immediately upon resolution."}
          </div>

          {/* Evidence Type */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1.5">
              Evidence / Proof Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { type: "photo", label: "Fixed Photo", icon: <Camera className="w-3.5 h-3.5" /> },
                { type: "maintenance_record", label: "Work Record / Slip", icon: <FileCheck className="w-3.5 h-3.5" /> },
                { type: "description", label: "Action Notes", icon: <FileText className="w-3.5 h-3.5" /> },
                { type: "screenshot", label: "System Screenshot", icon: <FileText className="w-3.5 h-3.5" /> },
              ].map((item) => (
                <button
                  key={item.type}
                  type="button"
                  onClick={() => setEvidenceType(item.type as EvidenceType)}
                  className={`flex items-center gap-2 p-2.5 rounded-xl border text-xs font-medium transition-all ${
                    evidenceType === item.type
                      ? "border-teal-600 bg-teal-50 text-teal-900 font-semibold"
                      : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Resolution Description */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Actions Taken & Resolution Details <span className="text-rose-500">*</span>
            </label>
            <textarea
              required
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="E.g., Replaced capacitor in fan #2 and verified quiet operation at all regulator speeds."
              className="w-full text-xs p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none"
            />
          </div>

          {/* Attachment URL */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Attachment / Evidence URL <span className="text-gray-400 font-normal">(optional photo/file link)</span>
            </label>
            <div className="relative">
              <LinkIcon className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
              <input
                type="url"
                value={attachmentUrl}
                onChange={(e) => setAttachmentUrl(e.target.value)}
                placeholder="https://example.com/repair_photo.jpg"
                className="w-full text-xs pl-9 pr-3 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none"
              />
            </div>
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
              className="px-5 py-2.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-xl shadow-md shadow-teal-600/20 transition-all disabled:opacity-50"
            >
              {loading ? "Submitting..." : "Submit Resolution & Evidence"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

