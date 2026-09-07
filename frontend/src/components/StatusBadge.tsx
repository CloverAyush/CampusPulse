import React from "react";
import { IssueStatus } from "@/lib/types";

interface StatusBadgeProps {
  status: IssueStatus | string;
  size?: "sm" | "md" | "lg";
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = "md" }) => {
  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs font-medium",
    md: "px-2.5 py-1 text-xs font-semibold",
    lg: "px-3 py-1.5 text-sm font-semibold",
  };

  const getStatusConfig = () => {
    switch (status) {
      case "OPEN":
        return {
          label: "Open / Routed",
          className: "bg-amber-50 text-amber-700 border-amber-200 ring-amber-500/20",
          dotColor: "bg-amber-500",
        };
      case "IN_PROGRESS":
        return {
          label: "In Progress",
          className: "bg-blue-50 text-blue-700 border-blue-200 ring-blue-500/20",
          dotColor: "bg-blue-500 animate-pulse",
        };
      case "ESCALATED":
        return {
          label: "Escalated to Authority",
          className: "bg-purple-50 text-purple-700 border-purple-200 ring-purple-500/20",
          dotColor: "bg-purple-500",
        };
      case "RESOLVED_PENDING_VERIFICATION":
        return {
          label: "Resolved (Pending Verification)",
          className: "bg-teal-50 text-teal-700 border-teal-200 ring-teal-500/20",
          dotColor: "bg-teal-500",
        };
      case "VERIFIED_CLOSED":
        return {
          label: "Verified & Closed",
          className: "bg-emerald-50 text-emerald-700 border-emerald-200 ring-emerald-500/20",
          dotColor: "bg-emerald-500",
        };
      case "REOPENED":
        return {
          label: "Reopened (Disputed)",
          className: "bg-rose-50 text-rose-700 border-rose-200 ring-rose-500/20",
          dotColor: "bg-rose-500 animate-ping",
        };
      default:
        return {
          label: status,
          className: "bg-gray-100 text-gray-700 border-gray-200",
          dotColor: "bg-gray-400",
        };
    }
  };

  const config = getStatusConfig();

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ring-1 ${config.className} ${sizeClasses[size]}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${config.dotColor}`} />
      {config.label}
    </span>
  );
};

