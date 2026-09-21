"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Loader2, Send } from "lucide-react";

import { DuplicatePromptModal } from "@/components/DuplicatePromptModal";
import { ErrorState, InlineError, LoadingState } from "@/components/States";
import { api, errorMessage } from "@/lib/api";
import { DuplicateIssueCandidate, IssueType, Location } from "@/lib/types";

const MIN_DESCRIPTION = 10;
const MAX_DESCRIPTION = 2000;

export default function ReportPage() {
  const router = useRouter();

  const [issueTypes, setIssueTypes] = useState<IssueType[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loadError, setLoadError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);

  const [category, setCategory] = useState("");
  const [issueTypeId, setIssueTypeId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [specificAsset, setSpecificAsset] = useState("");
  const [description, setDescription] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");

  const [candidates, setCandidates] = useState<DuplicateIssueCandidate[]>([]);
  const [promptOpen, setPromptOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const data = await api.getTaxonomies();
        if (cancelled) return;
        setIssueTypes(data.issue_types);
        setLocations(data.locations);
        setLoadError(null);
      } catch (cause) {
        if (!cancelled) setLoadError(cause);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const retryTaxonomies = useCallback(() => {
    setLoading(true);
    setReloadToken((token) => token + 1);
  }, []);

  const categories = useMemo(
    () => Array.from(new Set(issueTypes.map((type) => type.category))).sort(),
    [issueTypes]
  );
  const subTypes = useMemo(
    () => issueTypes.filter((type) => type.category === category),
    [issueTypes, category]
  );
  const locationsByBuilding = useMemo(() => {
    const grouped = new Map<string, Location[]>();
    locations.forEach((location) => {
      const bucket = grouped.get(location.building) ?? [];
      bucket.push(location);
      grouped.set(location.building, bucket);
    });
    return Array.from(grouped.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [locations]);

  const descriptionTooShort = description.trim().length < MIN_DESCRIPTION;
  const canSubmit = Boolean(issueTypeId) && Boolean(locationId) && !descriptionTooShort;

  const buildPayload = (existingIssueId?: number) => ({
    issue_type_id: Number(issueTypeId),
    location_id: Number(locationId),
    description: description.trim(),
    specific_asset: specificAsset.trim() || undefined,
    photo_url: photoUrl.trim() || undefined,
    existing_issue_id: existingIssueId,
  });

  const submit = async (existingIssueId?: number) => {
    setSubmitting(true);
    setError(null);
    try {
      const report = await api.submitReport(buildPayload(existingIssueId));
      setPromptOpen(false);
      router.push(report.issue_id ? `/issues/${report.issue_id}` : "/my-reports");
    } catch (cause) {
      setPromptOpen(false);
      setError(errorMessage(cause));
      setSubmitting(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setError(null);

    try {
      const duplicates = await api.checkDuplicate({
        issue_type_id: Number(issueTypeId),
        location_id: Number(locationId),
        specific_asset: specificAsset.trim() || undefined,
      });

      if (duplicates.has_match && duplicates.candidates.length > 0) {
        setCandidates(duplicates.candidates);
        setPromptOpen(true);
        setSubmitting(false);
        return;
      }
    } catch {
      // The duplicate check is an aid, not a gate. If it fails, the report still
      // goes through rather than blocking the student.
    }

    await submit();
  };

  if (loading) return <LoadingState label="Loading the report form" />;
  if (loadError) return <ErrorState error={loadError} onRetry={retryTaxonomies} />;

  return (
    <div className="mx-auto max-w-2xl">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Report an issue</h1>
        <p className="mt-1 text-sm text-gray-500">
          For shared campus problems: a broken fan, no Wi-Fi in a lab, an overflowing bin.
          Four fields and you are done.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-5 rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="category" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
              What kind of problem?
            </label>
            <select
              id="category"
              value={category}
              onChange={(event) => {
                setCategory(event.target.value);
                setIssueTypeId("");
              }}
              required
              className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            >
              <option value="">Select a category</option>
              {categories.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="sub_type" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
              More specifically
            </label>
            <select
              id="sub_type"
              value={issueTypeId}
              onChange={(event) => setIssueTypeId(event.target.value)}
              required
              disabled={!category}
              className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 disabled:bg-gray-50 disabled:text-gray-400"
            >
              <option value="">{category ? "Select the problem" : "Pick a category first"}</option>
              {subTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.sub_type}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label htmlFor="location" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
            Where is it?
          </label>
          <select
            id="location"
            value={locationId}
            onChange={(event) => setLocationId(event.target.value)}
            required
            className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          >
            <option value="">Select a location</option>
            {locationsByBuilding.map(([building, items]) => (
              <optgroup key={building} label={building}>
                {items.map((location) => (
                  <option key={location.id} value={location.id}>
                    {location.name}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="asset" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
            Which one exactly? <span className="font-medium normal-case text-gray-400">(optional)</span>
          </label>
          <input
            id="asset"
            value={specificAsset}
            onChange={(event) => setSpecificAsset(event.target.value)}
            maxLength={150}
            placeholder="Second fan from the door, third tap from the left…"
            className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <p className="mt-1 text-[11px] text-gray-400">
            This is what lets us tell your report apart from a different fan in the same room.
          </p>
        </div>

        <div>
          <label htmlFor="description" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
            What is wrong?
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            rows={4}
            required
            maxLength={MAX_DESCRIPTION}
            placeholder="The fan runs for a minute and then stops completely."
            className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <p className="mt-1 text-[11px] text-gray-400">
            {description.trim().length}/{MAX_DESCRIPTION} characters. Minimum {MIN_DESCRIPTION}.
          </p>
        </div>

        <div>
          <label htmlFor="photo" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
            Photo link <span className="font-medium normal-case text-gray-400">(optional)</span>
          </label>
          <input
            id="photo"
            type="url"
            inputMode="url"
            value={photoUrl}
            onChange={(event) => setPhotoUrl(event.target.value)}
            placeholder="https://drive.example.edu/broken-fan.jpg"
            className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <p className="mt-1 text-[11px] text-gray-400">
            Paste an https link to a photo you have already uploaded somewhere.
          </p>
        </div>

        <InlineError message={error} />

        <div className="flex items-center justify-between gap-3 border-t border-gray-100 pt-4">
          <p className="flex items-center gap-1.5 text-[11px] text-gray-400">
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
            Routed automatically to the right department.
          </p>
          <button
            type="submit"
            disabled={!canSubmit || submitting}
            className="inline-flex items-center gap-2 rounded-full bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Send className="h-4 w-4" aria-hidden />}
            {submitting ? "Submitting…" : "Submit report"}
          </button>
        </div>
      </form>

      <DuplicatePromptModal
        open={promptOpen}
        candidates={candidates}
        submitting={submitting}
        onClose={() => setPromptOpen(false)}
        onJoin={(issueId) => void submit(issueId)}
        onCreateSeparate={() => void submit()}
      />
    </div>
  );
}
