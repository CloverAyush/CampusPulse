import React from "react";
import { AlertOctagon, CheckCircle2, Clock, RotateCcw, ShieldAlert, Wrench } from "lucide-react";

import { STATUS_LABELS } from "@/lib/format";
import { IssueStatus } from "@/lib/types";

const STATUS_STYLES: Record<IssueStatus, { className: string; icon: React.ReactNode }> = {
  OPEN: {
    className: "bg-amber-50 text-amber-800 border-amber-200",
    icon: <Clock className="h-3 w-3" aria-hidden />,
  },
  IN_PROGRESS: {
    className: "bg-blue-50 text-blue-800 border-blue-200",
    icon: <Wrench className="h-3 w-3" aria-hidden />,
  },
  ESCALATED: {
    className: "bg-purple-50 text-purple-800 border-purple-200",
    icon: <ShieldAlert className="h-3 w-3" aria-hidden />,
  },
  RESOLVED_PENDING_VERIFICATION: {
    className: "bg-teal-50 text-teal-800 border-teal-200",
    icon: <AlertOctagon className="h-3 w-3" aria-hidden />,
  },
  VERIFIED_CLOSED: {
    className: "bg-emerald-50 text-emerald-800 border-emerald-200",
    icon: <CheckCircle2 className="h-3 w-3" aria-hidden />,
  },
  REOPENED: {
    className: "bg-rose-50 text-rose-800 border-rose-200",
    icon: <RotateCcw className="h-3 w-3" aria-hidden />,
  },
};

export const StatusBadge: React.FC<{ status: IssueStatus }> = ({ status }) => {
  const style = STATUS_STYLES[status];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${style.className}`}
    >
      {style.icon}
      {STATUS_LABELS[status]}
    </span>
  );
};
