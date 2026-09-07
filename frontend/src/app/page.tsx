"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Issue } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";
import {
  PlusCircle,
  Wrench,
  ShieldAlert,
  ArrowRight,
  MapPin,
  Users,
  Building,
  Zap,
  CheckCircle2,
  FileCheck2,
} from "lucide-react";

export default function HomePage() {
  const { user } = useAuth();
  const [recentIssues, setRecentIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecent = async () => {
      try {
        const issues = await api.getIssues();
        setRecentIssues(issues.slice(0, 6));
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    if (user) {
      fetchRecent();
    }
  }, [user]);

  return (
    <div className="space-y-10">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-900 via-slate-900 to-indigo-950 p-8 sm:p-12 text-white shadow-2xl border border-indigo-800/30">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-200 text-xs font-semibold">
            <Zap className="w-3.5 h-3.5 text-indigo-400" />
            <span>Deterministic Campus Infrastructure Platform</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Institutional Signal, <br />
            <span className="bg-gradient-to-r from-indigo-300 to-blue-200 bg-clip-text text-transparent">
              Zero Informal Friction.
            </span>
          </h1>

          <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl">
            CampusPulse turns scattered individual campus complaints into structured institutional
            signal. Pure deterministic routing, verified proof-of-resolution, and transparent escalation tracking.
          </p>

          {/* Role-Based Quick Actions */}
          <div className="pt-4 flex flex-wrap items-center gap-3">
            <Link
              href="/report"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-indigo-500 hover:bg-indigo-400 text-white font-semibold text-sm shadow-lg shadow-indigo-500/30 transition-all hover:scale-102"
            >
              <PlusCircle className="w-5 h-5" />
              <span>Report an Issue</span>
            </Link>

            {user?.role === "handler" && (
              <Link
                href="/handler"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-sm border border-white/20 transition-colors"
              >
                <Wrench className="w-4 h-4 text-blue-300" />
                <span>My Assigned Issues Queue</span>
              </Link>
            )}

            {user?.role === "higher_authority" && (
              <Link
                href="/higher-authority"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-sm shadow-lg shadow-purple-600/30 transition-all"
              >
                <ShieldAlert className="w-4 h-4" />
                <span>Review Escalated Cases</span>
              </Link>
            )}

            <Link
              href="/my-reports"
              className="inline-flex items-center gap-2 px-4 py-3 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-200 font-medium text-sm border border-slate-700 transition-colors"
            >
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
              <span>My Reports & Verification</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Core Principles Architecture Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-white rounded-3xl border border-gray-200/80 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
            1
          </div>
          <h3 className="text-base font-bold text-gray-900">
            Deterministic Routing
          </h3>
          <p className="text-xs text-gray-600 leading-relaxed">
            Routing rules map structured issue categories and locations directly to responsible handlers.
            No black-box AI or misrouted emails.
          </p>
        </div>

        <div className="p-6 bg-white rounded-3xl border border-gray-200/80 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center font-bold">
            2
          </div>
          <h3 className="text-base font-bold text-gray-900">
            Verifiable Resolution
          </h3>
          <p className="text-xs text-gray-600 leading-relaxed">
            Handlers attach mandatory evidence (photos, maintenance slips, notes). Affected students verify
            whether the problem is actually resolved.
          </p>
        </div>

        <div className="p-6 bg-white rounded-3xl border border-gray-200/80 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
            3
          </div>
          <h3 className="text-base font-bold text-gray-900">
            Audit-Grade Escalation
          </h3>
          <p className="text-xs text-gray-600 leading-relaxed">
            When budget or authority exceeds handler limits, issues escalate with full chronological case
            history preserved with zero summarization.
          </p>
        </div>
      </div>

      {/* Recent Campus Issues Stream */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-gray-900">
              Active Campus Issues
            </h2>
            <p className="text-xs text-gray-500">
              Current institutional issues undergoing resolution or verification.
            </p>
          </div>
          <Link
            href="/my-reports"
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((n) => (
              <div
                key={n}
                className="h-44 rounded-3xl bg-white border border-gray-200 animate-pulse"
              />
            ))}
          </div>
        ) : recentIssues.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-3xl border border-gray-200">
            <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
            <h3 className="text-sm font-bold text-gray-900">
              All Campus Issues Cleared
            </h3>
            <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
              No active open issues reported right now. Submit a new report if you notice any facility issue!
            </p>
            <div className="mt-4">
              <Link
                href="/report"
                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold"
              >
                <PlusCircle className="w-4 h-4" />
                <span>Submit Report</span>
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentIssues.map((issue) => (
              <Link
                key={issue.id}
                href={`/issues/${issue.id}`}
                className="group p-5 bg-white rounded-3xl border border-gray-200/90 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-full">
                      {issue.issue_type?.category || "General"}
                    </span>
                    <StatusBadge status={issue.status} size="sm" />
                  </div>

                  <h3 className="text-sm font-bold text-gray-900 group-hover:text-indigo-600 transition-colors line-clamp-1">
                    {issue.title}
                  </h3>

                  <p className="text-xs text-gray-600 line-clamp-2 leading-relaxed">
                    {issue.description}
                  </p>
                </div>

                <div className="pt-4 border-t border-gray-100 mt-4 flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-gray-400" />
                    <span className="truncate max-w-[120px]">
                      {issue.location?.name || "Campus"}
                    </span>
                  </div>

                  <div className="flex items-center gap-1 font-medium bg-gray-100 px-2 py-0.5 rounded-full text-[11px]">
                    <Users className="w-3 h-3 text-gray-500" />
                    <span>{issue.report_count} {issue.report_count === 1 ? "report" : "reports"}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
