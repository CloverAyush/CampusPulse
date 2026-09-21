"use client";

import React from "react";
import { AlertTriangle, Inbox, Loader2, RefreshCw, WifiOff } from "lucide-react";

import { ApiError } from "@/lib/api";

export const LoadingState: React.FC<{ label?: string }> = ({ label = "Loading" }) => (
  <div className="flex flex-col items-center justify-center gap-3 py-14 text-center" role="status" aria-live="polite">
    <Loader2 className="h-6 w-6 animate-spin text-indigo-600" aria-hidden />
    <p className="text-sm text-gray-500">{label}…</p>
  </div>
);

export const EmptyState: React.FC<{ title: string; hint?: string; action?: React.ReactNode }> = ({
  title,
  hint,
  action,
}) => (
  <div className="flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-gray-300 bg-white/60 py-14 text-center">
    <Inbox className="h-7 w-7 text-gray-400" aria-hidden />
    <p className="text-sm font-semibold text-gray-700">{title}</p>
    {hint ? <p className="max-w-sm text-xs text-gray-500">{hint}</p> : null}
    {action ? <div className="mt-2">{action}</div> : null}
  </div>
);

/** An empty list and a failed request look identical unless the failure is shown.
 *  A handler seeing "no issues" when the API is down is the worst outcome here. */
export const ErrorState: React.FC<{ error: unknown; onRetry?: () => void }> = ({ error, onRetry }) => {
  const isNetwork = error instanceof ApiError && error.isNetworkError;
  const message =
    error instanceof ApiError
      ? error.message
      : error instanceof Error
        ? error.message
        : "Something went wrong.";
  const requestId = error instanceof ApiError ? error.requestId : undefined;

  return (
    <div
      className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-red-200 bg-red-50 py-12 text-center"
      role="alert"
    >
      {isNetwork ? (
        <WifiOff className="h-7 w-7 text-red-500" aria-hidden />
      ) : (
        <AlertTriangle className="h-7 w-7 text-red-500" aria-hidden />
      )}
      <div>
        <p className="text-sm font-semibold text-red-900">Could not load this</p>
        <p className="mx-auto mt-1 max-w-md px-4 text-xs text-red-700">{message}</p>
        {requestId ? (
          <p className="mt-2 font-mono text-[10px] text-red-400">Reference: {requestId}</p>
        ) : null}
      </div>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 rounded-full border border-red-300 bg-white px-4 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-100"
        >
          <RefreshCw className="h-3.5 w-3.5" aria-hidden />
          Try again
        </button>
      ) : null}
    </div>
  );
};

export const InlineError: React.FC<{ message: string | null }> = ({ message }) =>
  message ? (
    <p className="flex items-start gap-1.5 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800" role="alert">
      <AlertTriangle className="mt-px h-3.5 w-3.5 shrink-0" aria-hidden />
      <span>{message}</span>
    </p>
  ) : null;
