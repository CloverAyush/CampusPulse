import React from "react";
import Link from "next/link";
import { AlertTriangle, MapPin, Users } from "lucide-react";

import { StatusBadge } from "@/components/StatusBadge";
import { formatRelative, pluralise } from "@/lib/format";
import { Issue } from "@/lib/types";

export const IssueCard: React.FC<{ issue: Issue; actions?: React.ReactNode }> = ({ issue, actions }) => (
  <article className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition hover:border-gray-300">
    <div className="flex flex-wrap items-start justify-between gap-2">
      <Link href={`/issues/${issue.id}`} className="group min-w-0">
        <h3 className="truncate text-sm font-semibold text-gray-900 group-hover:text-indigo-700">{issue.title}</h3>
        <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-gray-500">
          <span className="inline-flex items-center gap-1">
            <MapPin className="h-3 w-3" aria-hidden />
            {issue.location?.name ?? "Unknown location"}
          </span>
          <span className="inline-flex items-center gap-1">
            <Users className="h-3 w-3" aria-hidden />
            {pluralise(issue.affected_student_count, "student")} affected
          </span>
          <span>Updated {formatRelative(issue.updated_at)}</span>
        </p>
      </Link>
      <div className="flex shrink-0 items-center gap-1.5">
        {issue.needs_triage ? (
          <span className="inline-flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-0.5 text-[11px] font-semibold text-amber-800">
            <AlertTriangle className="h-3 w-3" aria-hidden />
            Needs triage
          </span>
        ) : null}
        <StatusBadge status={issue.status} />
      </div>
    </div>

    <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-gray-600">{issue.description}</p>

    <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-gray-100 pt-3">
      <p className="text-[11px] text-gray-500">
        {issue.current_handler ? `Handled by ${issue.current_handler.full_name}` : "Not yet assigned"}
      </p>
      {actions ? <div className="flex flex-wrap gap-1.5">{actions}</div> : null}
    </div>
  </article>
);
