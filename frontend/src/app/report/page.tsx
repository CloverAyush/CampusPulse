"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { IssueType, Location, DuplicateIssueCandidate } from "@/lib/types";
import { DuplicatePromptModal } from "@/components/DuplicatePromptModal";
import {
  Send,
  Camera,
  MapPin,
  Layers,
  FileText,
  Tag,
  CheckCircle,
  AlertCircle,
  Sparkles,
} from "lucide-react";

export default function ReportPage() {
  const router = useRouter();
  const { user } = useAuth();

  const [issueTypes, setIssueTypes] = useState<IssueType[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loadingTaxonomies, setLoadingTaxonomies] = useState(true);

  // Form State
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedIssueTypeId, setSelectedIssueTypeId] = useState<number | null>(null);
  const [selectedBuilding, setSelectedBuilding] = useState("");
  const [selectedLocationId, setSelectedLocationId] = useState<number | null>(null);
  const [specificAsset, setSpecificAsset] = useState("");
  const [description, setDescription] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");

  // Duplicate Check Modal State
  const [duplicateCandidates, setDuplicateCandidates] = useState<DuplicateIssueCandidate[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    const loadTaxonomies = async () => {
      try {
        const data = await api.getTaxonomies();
        setIssueTypes(data.issue_types);
        setLocations(data.locations);

        if (data.issue_types.length > 0) {
          const firstCat = data.issue_types[0].category;
          setSelectedCategory(firstCat);
          const firstType = data.issue_types.find((t) => t.category === firstCat);
          if (firstType) setSelectedIssueTypeId(firstType.id);
        }

        if (data.locations.length > 0) {
          const firstBldg = data.locations[0].building;
          setSelectedBuilding(firstBldg);
          const firstLoc = data.locations.find((l) => l.building === firstBldg);
          if (firstLoc) setSelectedLocationId(firstLoc.id);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load taxonomies");
      } finally {
        setLoadingTaxonomies(false);
      }
    };
    loadTaxonomies();
  }, []);

  // Filtered sub-types for selected category
  const categories = Array.from(new Set(issueTypes.map((t) => t.category)));
  const subTypesForCategory = issueTypes.filter((t) => t.category === selectedCategory);

  // Filtered locations for selected building
  const buildings = Array.from(new Set(locations.map((l) => l.building)));
  const locationsForBuilding = locations.filter((l) => l.building === selectedBuilding);

  const handleCategoryChange = (cat: string) => {
    setSelectedCategory(cat);
    const firstType = issueTypes.find((t) => t.category === cat);
    if (firstType) setSelectedIssueTypeId(firstType.id);
  };

  const handleBuildingChange = (bldg: string) => {
    setSelectedBuilding(bldg);
    const firstLoc = locations.filter((l) => l.building === bldg)[0];
    if (firstLoc) setSelectedLocationId(firstLoc.id);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIssueTypeId || !selectedLocationId || !description.trim()) {
      setError("Please fill in all mandatory fields (Issue Type, Location, and Description).");
      return;
    }

    setError(null);
    setSubmitting(true);

    try {
      // 1. Run deterministic duplicate check
      const checkRes = await api.checkDuplicate({
        issue_type_id: selectedIssueTypeId,
        location_id: selectedLocationId,
        specific_asset: specificAsset.trim() || undefined,
      });

      if (checkRes.has_match && checkRes.candidates.length > 0) {
        // Match found! Present prompt to student
        setDuplicateCandidates(checkRes.candidates);
        setIsModalOpen(true);
        setSubmitting(false);
      } else {
        // No match found -> create new issue directly
        await executeReportSubmission(undefined);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to check duplicates");
      setSubmitting(false);
    }
  };

  const executeReportSubmission = async (existingIssueId?: number) => {
    setSubmitting(true);
    setError(null);
    try {
      const report = await api.submitReport({
        issue_type_id: selectedIssueTypeId!,
        location_id: selectedLocationId!,
        specific_asset: specificAsset.trim() || undefined,
        description: description.trim(),
        photo_url: photoUrl.trim() || undefined,
        existing_issue_id: existingIssueId,
      });

      setIsModalOpen(false);
      setSuccessMsg(
        existingIssueId
          ? "Your report has been successfully linked to the existing campus issue!"
          : "Your report has been successfully submitted and deterministically routed to the responsible handler."
      );

      setTimeout(() => {
        router.push("/my-reports");
      }, 1500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to submit report");
    } finally {
      setSubmitting(false);
    }
  };

  const handleConfirmJoin = (issueId: number) => {
    executeReportSubmission(issueId);
  };

  const handleCreateNewDistinct = () => {
    executeReportSubmission(undefined);
  };

  if (loadingTaxonomies) {
    return (
      <div className="max-w-2xl mx-auto p-12 text-center">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-xs text-gray-500 font-medium">Loading campus taxonomy...</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2.5">
          <Send className="w-6 h-6 text-indigo-600" />
          <span>Report an Institutional Issue</span>
        </h1>
        <p className="text-xs text-gray-500 leading-relaxed">
          Tell us <strong>what</strong> is wrong and <strong>where</strong> it is. The platform handles
          deterministic routing directly to the responsible handler.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-center gap-3 text-xs text-rose-700 font-medium animate-in fade-in">
          <AlertCircle className="w-5 h-5 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center gap-3 text-xs text-emerald-800 font-medium animate-in fade-in">
          <CheckCircle className="w-5 h-5 shrink-0 text-emerald-600" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Main Submission Form */}
      <form onSubmit={handleFormSubmit} className="bg-white rounded-3xl border border-gray-200/90 shadow-sm p-6 sm:p-8 space-y-6">
        {/* Step 1: Issue Classification */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-gray-100 text-xs font-bold uppercase tracking-wider text-gray-400">
            <Tag className="w-4 h-4 text-indigo-600" />
            <span>1. What is the issue type?</span>
          </div>

          {/* Category Chips */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-2">
              Issue Category <span className="text-rose-500">*</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {categories.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => handleCategoryChange(cat)}
                  className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
                    selectedCategory === cat
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/20"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Specific Sub-type */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1.5">
              Specific Problem Sub-Type <span className="text-rose-500">*</span>
            </label>
            <select
              value={selectedIssueTypeId || ""}
              onChange={(e) => setSelectedIssueTypeId(Number(e.target.value))}
              className="w-full text-xs p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white font-medium"
            >
              {subTypesForCategory.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.sub_type} {type.description ? `— (${type.description})` : ""}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Step 2: Structured Location */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-gray-100 text-xs font-bold uppercase tracking-wider text-gray-400">
            <MapPin className="w-4 h-4 text-indigo-600" />
            <span>2. Where is it located?</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Building Selector */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                Building / Wing <span className="text-rose-500">*</span>
              </label>
              <select
                value={selectedBuilding}
                onChange={(e) => handleBuildingChange(e.target.value)}
                className="w-full text-xs p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white font-medium"
              >
                {buildings.map((bldg) => (
                  <option key={bldg} value={bldg}>
                    {bldg}
                  </option>
                ))}
              </select>
            </div>

            {/* Room / Area Selector */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                Specific Room / Area <span className="text-rose-500">*</span>
              </label>
              <select
                value={selectedLocationId || ""}
                onChange={(e) => setSelectedLocationId(Number(e.target.value))}
                className="w-full text-xs p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white font-medium"
              >
                {locationsForBuilding.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name} {loc.floor ? `(${loc.floor})` : ""}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Specific Asset Tag */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Specific Asset Tag / Object Identifier <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              type="text"
              value={specificAsset}
              onChange={(e) => setSpecificAsset(e.target.value)}
              placeholder="E.g., Fan #2, Back-row switchboard, Tap #3, Router AP-04"
              className="w-full text-xs p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            />
          </div>
        </div>

        {/* Step 3: Description & Proof */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-gray-100 text-xs font-bold uppercase tracking-wider text-gray-400">
            <FileText className="w-4 h-4 text-indigo-600" />
            <span>3. Describe the problem</span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Description <span className="text-rose-500">*</span>
            </label>
            <textarea
              required
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what is broken or malfunctioning clearly so the handler can bring the right tools/parts..."
              className="w-full text-xs p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none leading-relaxed"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Photo URL <span className="text-gray-400 font-normal">(optional image proof)</span>
            </label>
            <div className="relative">
              <Camera className="w-4 h-4 text-gray-400 absolute left-3.5 top-3" />
              <input
                type="url"
                value={photoUrl}
                onChange={(e) => setPhotoUrl(e.target.value)}
                placeholder="https://example.com/broken_fan.jpg"
                className="w-full text-xs pl-10 pr-3 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              />
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-4 border-t border-gray-100 flex items-center justify-between">
          <div className="text-[11px] text-gray-400 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            <span>Deterministic routing config will assign the responsible staff.</span>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-lg shadow-indigo-500/20 transition-all hover:scale-102 disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
            <span>{submitting ? "Checking & Submitting..." : "Submit Report"}</span>
          </button>
        </div>
      </form>

      {/* Deterministic Duplicate Suggestion Modal */}
      <DuplicatePromptModal
        isOpen={isModalOpen}
        candidates={duplicateCandidates}
        onConfirmJoin={handleConfirmJoin}
        onCreateNew={handleCreateNewDistinct}
        onCancel={() => setIsModalOpen(false)}
        submitting={submitting}
      />
    </div>
  );
}

