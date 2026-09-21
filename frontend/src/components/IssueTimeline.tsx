import React from "react";
import {
  ArrowRightLeft,
  CheckCircle2,
  FilePlus2,
  Link2,
  RotateCcw,
  Route,
  ShieldAlert,
  ThumbsDown,
  Wrench,
} from "lucide-react";

import { formatDateTime } from "@/lib/format";
import { TimelineEvent, TimelineEventType } from "@/lib/types";

const EVENT_STYLES: Record<TimelineEventType, { icon: React.ReactNode; ring: string }> = {
  REPORT_SUBMITTED: { icon: <FilePlus2 className="h-3.5 w-3.5" aria-hidden />, ring: "bg-indigo-100 text-indigo-700" },
  REPORT_LINKED: { icon: <Link2 className="h-3.5 w-3.5" aria-hidden />, ring: "bg-indigo-100 text-indigo-700" },
  ISSUE_CREATED: { icon: <FilePlus2 className="h-3.5 w-3.5" aria-hidden />, ring: "bg-indigo-100 text-indigo-700" },
  ROUTED: { icon: <Route className="h-3.5 w-3.5" aria-hidden />, ring: "bg-sky-100 text-sky-700" },
  STATUS_CHANGED: { icon: <ArrowRightLeft className="h-3.5 w-3.5" aria-hidden />, ring: "bg-gray-100 text-gray-700" },
  STARTED_PROGRESS: { icon: <Wrench className="h-3.5 w-3.5" aria-hidden />, ring: "bg-blue-100 text-blue-700" },
  RESOLVED: { icon: <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />, ring: "bg-teal-100 text-teal-700" },
  ESCALATED: { icon: <ShieldAlert className="h-3.5 w-3.5" aria-hidden />, ring: "bg-purple-100 text-purple-700" },
  VERIFIED: { icon: <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />, ring: "bg-emerald-100 text-emerald-700" },
  DISPUTED: { icon: <ThumbsDown className="h-3.5 w-3.5" aria-hidden />, ring: "bg-rose-100 text-rose-700" },
  REOPENED: { icon: <RotateCcw className="h-3.5 w-3.5" aria-hidden />, ring: "bg-rose-100 text-rose-700" },
  REASSIGNED: { icon: <ArrowRightLeft className="h-3.5 w-3.5" aria-hidden />, ring: "bg-amber-100 text-amber-700" },
};

export const IssueTimeline: React.FC<{ events: TimelineEvent[] }> = ({ events }) => {
  if (events.length === 0) {
    return <p className="py-6 text-center text-xs text-gray-400">No history recorded yet.</p>;
  }

  return (
    <ol className="relative space-y-5 border-l border-gray-200 pl-6">
      {events.map((event) => {
        const style = EVENT_STYLES[event.event_type];
        return (
          <li key={event.id} className="relative">
            <span
              className={`absolute -left-[31px] grid h-6 w-6 place-items-center rounded-full ring-4 ring-white ${style.ring}`}
            >
              {style.icon}
            </span>
            <div className="flex flex-wrap items-baseline justify-between gap-x-3">
              <p className="text-sm font-semibold text-gray-900">{event.title}</p>
              <time dateTime={event.created_at} className="text-[11px] text-gray-400">
                {formatDateTime(event.created_at)}
              </time>
            </div>
            {event.details ? (
              <p className="mt-1 whitespace-pre-line text-xs leading-relaxed text-gray-600">{event.details}</p>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
};
