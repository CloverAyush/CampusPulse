"use client";

import React from "react";
import { DuplicateIssueCandidate } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";
import { AlertTriangle, Users, MapPin, Tag, ArrowRight, PlusCircle, ArrowLeft } from "lucide-react";

interface DuplicatePromptModalProps {
  isOpen: boolean;
  candidates: DuplicateIssueCandidate[];
  onConfirmJoin: (issueId: number) => void;
  onCreateNew: () => void;
  onCancel: () => void;
  submitting?: boolean;
}

export const DuplicatePromptModal: React.FC<DuplicatePromptModalProps> = ({
  isOpen,
  candidates,
  onConfirmJoin,
  onCreateNew,
  onCancel,
  submitting = false,
}) => {
  if (!isOpen || candidates.length === 0) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col border border-gray-100 overflow-hidden">
        {/* Header */}
        <div className="bg-amber-500/10 px-6 py-5 border-b border-amber-200/60 flex items-start gap-4">
          <div className="p-3 bg-amber-500 text-white rounded-2xl shadow-md shadow-amber-500/20">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">
              Possible Existing Issue Detected
            </h3>
            <p className="text-xs text-amber-900/80 mt-1 leading-relaxed">
              We found an active problem already reported at this exact location. Linking your report
              strengthens the institutional priority instead of creating redundant tickets.
            </p>
          </div>
        </div>

        {/* Candidate List */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          <div className="text-xs font-semibold uppercase tracking-wider text-gray-400">
            Matching Existing Active Issue(s)
          </div>

          {candidates.map((candidate) => (
            <div
              key={candidate.issue_id}
              className="p-5 rounded-2xl border-2 border-indigo-100 bg-indigo-50/30 hover:border-indigo-300 transition-all space-y-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h4 className="text-base font-bold text-gray-900">
                  {candidate.title}
                </h4>
                <StatusBadge status={candidate.status} size="sm" />
              </div>

              <div className="flex flex-wrap items-center gap-4 text-xs text-gray-600">
                <div className="flex items-center gap-1.5 font-medium">
                  <MapPin className="w-3.5 h-3.5 text-indigo-600" />
                  <span>{candidate.location_name}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Tag className="w-3.5 h-3.5 text-indigo-600" />
                  <span>{candidate.issue_category} &rarr; {candidate.issue_sub_type}</span>
                </div>
                <div className="flex items-center gap-1.5 bg-indigo-100/70 text-indigo-800 px-2 py-0.5 rounded-full font-semibold">
                  <Users className="w-3.5 h-3.5" />
                  <span>{candidate.report_count} {candidate.report_count === 1 ? "student report" : "student reports"} linked</span>
                </div>
              </div>

              <div className="text-xs text-gray-700 bg-white/80 p-3 rounded-xl border border-indigo-100/60 leading-relaxed">
                <span className="font-semibold text-gray-900">Report details: </span>
                {candidate.description}
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => onConfirmJoin(candidate.issue_id)}
                  className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-indigo-500/20 transition-all hover:translate-x-0.5"
                >
                  <span>Yes, This is the Same Issue (Link Report)</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Footer Actions */}
        <div className="bg-gray-50 px-6 py-4 border-t border-gray-100 flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-200/60 rounded-xl transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Go Back & Edit</span>
          </button>

          <button
            type="button"
            disabled={submitting}
            onClick={onCreateNew}
            className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-gray-800 bg-white hover:bg-gray-100 border border-gray-300 rounded-xl shadow-sm transition-all"
          >
            <PlusCircle className="w-4 h-4 text-gray-500" />
            <span>No, This is a Different Issue (Create New)</span>
          </button>
        </div>
      </div>
    </div>
  );
};

