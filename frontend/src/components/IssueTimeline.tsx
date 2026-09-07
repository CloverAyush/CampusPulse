"use client";

import React from "react";
import { TimelineEvent, TimelineEventType } from "@/lib/types";
import {
  FileText,
  GitCommit,
  PlayCircle,
  AlertOctagon,
  CheckCircle2,
  XCircle,
  RefreshCw,
  UserCheck,
  Tag,
} from "lucide-react";

interface IssueTimelineProps {
  events: TimelineEvent[];
}

export const IssueTimeline: React.FC<IssueTimelineProps> = ({ events }) => {
  if (!events || events.length === 0) {
    return (
      <div className="py-8 text-center text-xs text-gray-400">
        No history events recorded yet.
      </div>
    );
  }

  const getEventIcon = (type: TimelineEventType) => {
    switch (type) {
      case "REPORT_SUBMITTED":
        return <FileText className="w-4 h-4 text-emerald-600" />;
      case "REPORT_LINKED":
        return <Tag className="w-4 h-4 text-indigo-600" />;
      case "ISSUE_CREATED":
        return <GitCommit className="w-4 h-4 text-blue-600" />;
      case "ROUTED":
        return <UserCheck className="w-4 h-4 text-blue-600" />;
      case "STARTED_PROGRESS":
        return <PlayCircle className="w-4 h-4 text-blue-600" />;
      case "ESCALATED":
        return <AlertOctagon className="w-4 h-4 text-purple-600" />;
      case "RESOLVED":
        return <CheckCircle2 className="w-4 h-4 text-teal-600" />;
      case "VERIFIED":
        return <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
      case "DISPUTED":
      case "REOPENED":
        return <XCircle className="w-4 h-4 text-rose-600" />;
      case "REASSIGNED":
        return <RefreshCw className="w-4 h-4 text-amber-600" />;
      default:
        return <GitCommit className="w-4 h-4 text-gray-500" />;
    }
  };

  const getEventBorderColor = (type: TimelineEventType) => {
    switch (type) {
      case "REPORT_SUBMITTED":
      case "VERIFIED":
        return "border-emerald-500/30 bg-emerald-50/20";
      case "ESCALATED":
        return "border-purple-500/30 bg-purple-50/20";
      case "RESOLVED":
        return "border-teal-500/30 bg-teal-50/20";
      case "DISPUTED":
      case "REOPENED":
        return "border-rose-500/30 bg-rose-50/20";
      case "STARTED_PROGRESS":
      case "ROUTED":
        return "border-blue-500/30 bg-blue-50/20";
      default:
        return "border-gray-200 bg-gray-50/50";
    }
  };

  return (
    <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-200">
      {events.map((event) => {
        const dateStr = new Date(event.created_at).toLocaleString([], {
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        });

        return (
          <div key={event.id} className="relative group">
            {/* Timeline Node Icon */}
            <div className="absolute -left-6 mt-1 flex items-center justify-center w-6 h-6 rounded-full bg-white border-2 border-gray-300 shadow-sm group-hover:scale-110 transition-transform">
              {getEventIcon(event.event_type)}
            </div>

            {/* Event Card */}
            <div
              className={`p-4 rounded-2xl border ${getEventBorderColor(
                event.event_type
              )} shadow-sm transition-all hover:shadow-md space-y-1.5`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-bold text-gray-900">
                  {event.title}
                </span>
                <span className="text-[11px] font-medium text-gray-400">
                  {dateStr}
                </span>
              </div>

              {event.actor && (
                <div className="text-[11px] text-gray-500 flex items-center gap-1.5">
                  <span className="font-semibold text-gray-700">Action by:</span>
                  <span>{event.actor.full_name} ({event.actor.role.replace("_", " ")})</span>
                </div>
              )}

              {event.details && (
                <p className="text-xs text-gray-700 whitespace-pre-line bg-white/70 p-2.5 rounded-xl border border-gray-100 mt-1 leading-relaxed">
                  {event.details}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

