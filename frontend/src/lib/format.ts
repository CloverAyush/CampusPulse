import { IssueStatus } from "./types";

/** The API sends UTC with an explicit offset. Parsing it and rendering in the
 *  viewer's own locale is the only place timezone conversion should happen. */
export function formatDateTime(isoTimestamp: string): string {
  return new Date(isoTimestamp).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDate(isoTimestamp: string): string {
  return new Date(isoTimestamp).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatRelative(isoTimestamp: string): string {
  const elapsedMs = Date.now() - new Date(isoTimestamp).getTime();
  const minutes = Math.round(elapsedMs / 60000);

  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;

  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;

  const days = Math.round(hours / 24);
  if (days < 30) return `${days} day${days === 1 ? "" : "s"} ago`;

  return formatDate(isoTimestamp);
}

export const STATUS_LABELS: Record<IssueStatus, string> = {
  OPEN: "Open",
  IN_PROGRESS: "In progress",
  ESCALATED: "Escalated",
  RESOLVED_PENDING_VERIFICATION: "Awaiting your confirmation",
  VERIFIED_CLOSED: "Closed",
  REOPENED: "Reopened",
};

export function pluralise(count: number, singular: string, plural?: string): string {
  return `${count} ${count === 1 ? singular : plural ?? `${singular}s`}`;
}

const SAFE_LINK_PATTERN = /^https:\/\//i;

/** Server-side validation is the real control; this stops an unexpected value from
 *  ever reaching an href if the API is changed or stubbed. */
export function safeExternalUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  return SAFE_LINK_PATTERN.test(url.trim()) ? url.trim() : null;
}
