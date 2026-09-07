"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { IssueType, Location, RoutingRule, User } from "@/lib/types";
import {
  Settings,
  Layers,
  MapPin,
  GitFork,
  Plus,
  Trash2,
  RefreshCw,
  Database,
  CheckCircle,
  ShieldAlert,
  ArrowRight,
} from "lucide-react";

export default function AdminConfigPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"rules" | "types" | "locations">("rules");
  const [issueTypes, setIssueTypes] = useState<IssueType[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [routingRules, setRoutingRules] = useState<RoutingRule[]>([]);
  const [handlers, setHandlers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // New Rule Form State
  const [newRuleTypeId, setNewRuleTypeId] = useState<string>("");
  const [newRuleLocId, setNewRuleLocId] = useState<string>("");
  const [newRuleHandlerId, setNewRuleHandlerId] = useState<string>("");
  const [newRulePriority, setNewRulePriority] = useState<number>(10);

  // New Issue Type Form State
  const [newCategory, setNewCategory] = useState("");
  const [newSubType, setNewSubType] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newRequiresVerification, setNewRequiresVerification] = useState(true);

  // New Location Form State
  const [newLocName, setNewLocName] = useState("");
  const [newLocCode, setNewLocCode] = useState("");
  const [newLocBuilding, setNewLocBuilding] = useState("");
  const [newLocFloor, setNewLocFloor] = useState("");
  const [newLocRoom, setNewLocRoom] = useState("");

  const loadAll = async () => {
    setLoading(true);
    try {
      const [types, locs, rules, usersList] = await Promise.all([
        api.listIssueTypes(),
        api.listLocations(),
        api.listRoutingRules(),
        api.listUsers(),
      ]);
      setIssueTypes(types);
      setLocations(locs);
      setRoutingRules(rules);
      setHandlers(usersList.filter((u) => u.role === "handler" || u.role === "admin"));
      if (usersList.length > 0 && !newRuleHandlerId) {
        setNewRuleHandlerId(String(usersList[0].id));
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      loadAll();
    }
  }, [user]);

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRuleHandlerId) return;
    try {
      await api.createRoutingRule({
        issue_type_id: newRuleTypeId ? Number(newRuleTypeId) : null,
        location_id: newRuleLocId ? Number(newRuleLocId) : null,
        handler_id: Number(newRuleHandlerId),
        priority: Number(newRulePriority),
      });
      setToastMsg("Deterministic routing rule added successfully!");
      loadAll();
      setTimeout(() => setToastMsg(null), 3000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to create rule");
    }
  };

  const handleDeleteRule = async (id: number) => {
    if (!confirm("Are you sure you want to delete this routing rule?")) return;
    try {
      await api.deleteRoutingRule(id);
      setToastMsg("Routing rule removed.");
      loadAll();
      setTimeout(() => setToastMsg(null), 3000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete rule");
    }
  };

  const handleCreateType = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCategory.trim() || !newSubType.trim()) return;
    try {
      await api.createIssueType({
        category: newCategory.trim(),
        sub_type: newSubType.trim(),
        description: newDesc.trim() || undefined,
        requires_verification: newRequiresVerification,
        is_active: true,
      });
      setNewCategory("");
      setNewSubType("");
      setNewDesc("");
      setToastMsg("Issue type taxonomy created successfully!");
      loadAll();
      setTimeout(() => setToastMsg(null), 3000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to create issue type");
    }
  };

  const handleCreateLocation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLocName.trim() || !newLocCode.trim() || !newLocBuilding.trim()) return;
    try {
      await api.createLocation({
        name: newLocName.trim(),
        code: newLocCode.trim(),
        building: newLocBuilding.trim(),
        floor: newLocFloor.trim() || undefined,
        room: newLocRoom.trim() || undefined,
        is_active: true,
      });
      setNewLocName("");
      setNewLocCode("");
      setNewLocBuilding("");
      setNewLocFloor("");
      setNewLocRoom("");
      setToastMsg("Campus location added successfully!");
      loadAll();
      setTimeout(() => setToastMsg(null), 3000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to create location");
    }
  };

  const handleResetSeedData = async () => {
    if (!confirm("Reset database with standard campus demo dataset?")) return;
    try {
      await api.triggerSeedData();
      setToastMsg("Database re-seeded with clean campus demo data.");
      loadAll();
      setTimeout(() => setToastMsg(null), 3000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to seed data");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2.5">
            <Settings className="w-6 h-6 text-slate-700" />
            <span>Campus Configuration & Deterministic Rules</span>
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Manage issue taxonomies, structured locations hierarchy, and deterministic routing lookup tables.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleResetSeedData}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-xl shadow-sm transition-colors"
          >
            <Database className="w-3.5 h-3.5 text-indigo-600" />
            <span>Reset Demo Seed Data</span>
          </button>

          <button
            onClick={loadAll}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-xl transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {toastMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center gap-3 text-xs text-emerald-800 font-medium animate-in fade-in">
          <CheckCircle className="w-5 h-5 shrink-0 text-emerald-600" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-gray-200 gap-6 text-xs font-semibold">
        <button
          onClick={() => setActiveTab("rules")}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "rules"
              ? "border-indigo-600 text-indigo-600 font-bold"
              : "border-transparent text-gray-500 hover:text-gray-800"
          }`}
        >
          <GitFork className="w-4 h-4" />
          <span>Deterministic Routing Rules ({routingRules.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("types")}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "types"
              ? "border-indigo-600 text-indigo-600 font-bold"
              : "border-transparent text-gray-500 hover:text-gray-800"
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Issue Types & Verification Policies ({issueTypes.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("locations")}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "locations"
              ? "border-indigo-600 text-indigo-600 font-bold"
              : "border-transparent text-gray-500 hover:text-gray-800"
          }`}
        >
          <MapPin className="w-4 h-4" />
          <span>Locations Hierarchy ({locations.length})</span>
        </button>
      </div>

      {/* Tab 1: Routing Rules Table */}
      {activeTab === "rules" && (
        <div className="space-y-6">
          {/* Add Rule Card */}
          <div className="bg-white rounded-3xl border border-gray-200/90 shadow-sm p-6 space-y-4">
            <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <Plus className="w-4 h-4 text-indigo-600" />
              <span>Add Deterministic Routing Rule</span>
            </h3>
            <p className="text-xs text-gray-500">
              Rules map (Issue Type + Location) to a responsible handler with priority-based precedence.
            </p>

            <form onSubmit={handleCreateRule} className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <label className="block text-[11px] font-semibold text-gray-700 mb-1">Issue Type</label>
                <select
                  value={newRuleTypeId}
                  onChange={(e) => setNewRuleTypeId(e.target.value)}
                  className="w-full p-2.5 border border-gray-200 rounded-xl outline-none bg-white font-medium"
                >
                  <option value="">Any Issue Type (Global / Location Level)</option>
                  {issueTypes.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.category} &rarr; {t.sub_type}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-gray-700 mb-1">Location</label>
                <select
                  value={newRuleLocId}
                  onChange={(e) => setNewRuleLocId(e.target.value)}
                  className="w-full p-2.5 border border-gray-200 rounded-xl outline-none bg-white font-medium"
                >
                  <option value="">Any Location (Campus-Wide)</option>
                  {locations.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.name} ({l.building})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-gray-700 mb-1">Responsible Handler</label>
                <select
                  required
                  value={newRuleHandlerId}
                  onChange={(e) => setNewRuleHandlerId(e.target.value)}
                  className="w-full p-2.5 border border-gray-200 rounded-xl outline-none bg-white font-medium"
                >
                  {handlers.map((h) => (
                    <option key={h.id} value={h.id}>
                      {h.full_name} ({h.department || "Staff"})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <label className="block text-[11px] font-semibold text-gray-700 mb-1">Priority (1-100)</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={newRulePriority}
                    onChange={(e) => setNewRulePriority(Number(e.target.value))}
                    className="w-full p-2 border border-gray-200 rounded-xl outline-none"
                  />
                </div>
                <button
                  type="submit"
                  className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-sm transition-all"
                >
                  Add Rule
                </button>
              </div>
            </form>
          </div>

          {/* Rules Table */}
          <div className="bg-white rounded-3xl border border-gray-200/90 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 font-bold text-xs text-gray-900 uppercase tracking-wider">
              Active Routing Lookup Precedence
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-gray-50/80 text-gray-500 font-semibold border-b border-gray-100">
                  <tr>
                    <th className="px-6 py-3">Priority</th>
                    <th className="px-6 py-3">Issue Type</th>
                    <th className="px-6 py-3">Location Scope</th>
                    <th className="px-6 py-3">Assigned Handler</th>
                    <th className="px-6 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {routingRules.map((rule) => (
                    <tr key={rule.id} className="hover:bg-gray-50/50">
                      <td className="px-6 py-3.5">
                        <span className="font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full">
                          {rule.priority}
                        </span>
                      </td>
                      <td className="px-6 py-3.5 font-medium text-gray-900">
                        {rule.issue_type
                          ? `${rule.issue_type.category} → ${rule.issue_type.sub_type}`
                          : "Any (Global Type)"}
                      </td>
                      <td className="px-6 py-3.5 text-gray-600">
                        {rule.location ? rule.location.name : "Any (Campus-Wide)"}
                      </td>
                      <td className="px-6 py-3.5 font-semibold text-gray-800">
                        {rule.handler?.full_name || `User #${rule.handler_id}`}
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <button
                          onClick={() => handleDeleteRule(rule.id)}
                          className="text-gray-400 hover:text-rose-600 p-1.5 rounded-lg transition-colors"
                          title="Delete Rule"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Issue Types & Verification Policies */}
      {activeTab === "types" && (
        <div className="space-y-6">
          {/* Add Type Form */}
          <div className="bg-white rounded-3xl border border-gray-200/90 shadow-sm p-6 space-y-4">
            <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <Plus className="w-4 h-4 text-indigo-600" />
              <span>Create Issue Type Taxonomy</span>
            </h3>

            <form onSubmit={handleCreateType} className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <label className="block text-[11px] font-semibold text-gray-700 mb-1">Category</label>
                <input
                  required
                  type="text"
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  placeholder="E.g., Electrical, Plumbing, Wi-Fi"
                  className="w-full p-2.5 border border-gray-200 rounded-xl outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-gray-700 mb-1">Sub-Type</label>
                <input
                  required
                  type="text"
                  value={newSubType}
                  onChange={(e) => setNewSubType(e.target.value)}
                  placeholder="E.g., Ceiling Fan, Tap Leakage"
                  className="w-full p-2.5 border border-gray-200 rounded-xl outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-gray-700 mb-1">Description / Notes</label>
                <input
                  type="text"
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Short description..."
                  className="w-full p-2.5 border border-gray-200 rounded-xl outline-none"
                />
              </div>

              <div className="flex items-end justify-between gap-3">
                <label className="flex items-center gap-2 cursor-pointer pb-2 text-[11px] font-semibold text-gray-700">
                  <input
                    type="checkbox"
                    checked={newRequiresVerification}
                    onChange={(e) => setNewRequiresVerification(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                  />
                  <span>Requires Verification</span>
                </label>
                <button
                  type="submit"
                  className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-sm transition-all"
                >
                  Add Type
                </button>
              </div>
            </form>
          </div>

          {/* Types Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {issueTypes.map((type) => (
              <div
                key={type.id}
                className="p-5 bg-white rounded-3xl border border-gray-200/90 shadow-sm flex items-start justify-between gap-3"
              >
                <div className="space-y-1">
                  <span className="text-[11px] font-bold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-full">
                    {type.category}
                  </span>
                  <h4 className="text-sm font-bold text-gray-900 mt-1">{type.sub_type}</h4>
                  {type.description && <p className="text-xs text-gray-500">{type.description}</p>}
                </div>

                <div className="text-right">
                  <span
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${
                      type.requires_verification
                        ? "bg-teal-50 text-teal-700 border-teal-200"
                        : "bg-gray-100 text-gray-600 border-gray-200"
                    }`}
                  >
                    {type.requires_verification ? "Student Verification Req." : "Direct Close"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Locations Hierarchy */}
      {activeTab === "locations" && (
        <div className="space-y-6">
          {/* Add Location Form */}
          <div className="bg-white rounded-3xl border border-gray-200/90 shadow-sm p-6 space-y-4">
            <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <Plus className="w-4 h-4 text-indigo-600" />
              <span>Add Campus Location</span>
            </h3>

            <form onSubmit={handleCreateLocation} className="grid grid-cols-1 sm:grid-cols-5 gap-3 text-xs">
              <div>
                <label className="block text-[11px] font-semibold text-gray-700 mb-1">Location Name</label>
                <input
                  required
                  type="text"
                  value={newLocName}
                  onChange={(e) => setNewLocName(e.target.value)}
                  placeholder="Room 204 (Classroom)"
                  className="w-full p-2.5 border border-gray-200 rounded-xl outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-gray-700 mb-1">Code</label>
                <input
                  required
                  type="text"
                  value={newLocCode}
                  onChange={(e) => setNewLocCode(e.target.value)}
                  placeholder="BLK-A-RM-204"
                  className="w-full p-2.5 border border-gray-200 rounded-xl outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-gray-700 mb-1">Building</label>
                <input
                  required
                  type="text"
                  value={newLocBuilding}
                  onChange={(e) => setNewLocBuilding(e.target.value)}
                  placeholder="Block A"
                  className="w-full p-2.5 border border-gray-200 rounded-xl outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-gray-700 mb-1">Floor</label>
                <input
                  type="text"
                  value={newLocFloor}
                  onChange={(e) => setNewLocFloor(e.target.value)}
                  placeholder="2nd Floor"
                  className="w-full p-2.5 border border-gray-200 rounded-xl outline-none"
                />
              </div>

              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <label className="block text-[11px] font-semibold text-gray-700 mb-1">Room</label>
                  <input
                    type="text"
                    value={newLocRoom}
                    onChange={(e) => setNewLocRoom(e.target.value)}
                    placeholder="Room 204"
                    className="w-full p-2 border border-gray-200 rounded-xl outline-none"
                  />
                </div>
                <button
                  type="submit"
                  className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-sm transition-all"
                >
                  Add
                </button>
              </div>
            </form>
          </div>

          {/* Locations Table */}
          <div className="bg-white rounded-3xl border border-gray-200/90 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-gray-50/80 text-gray-500 font-semibold border-b border-gray-100">
                  <tr>
                    <th className="px-6 py-3">Location Name</th>
                    <th className="px-6 py-3">Code</th>
                    <th className="px-6 py-3">Building</th>
                    <th className="px-6 py-3">Floor</th>
                    <th className="px-6 py-3">Room</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {locations.map((loc) => (
                    <tr key={loc.id} className="hover:bg-gray-50/50">
                      <td className="px-6 py-3.5 font-bold text-gray-900">{loc.name}</td>
                      <td className="px-6 py-3.5 font-mono text-gray-500">{loc.code}</td>
                      <td className="px-6 py-3.5 text-gray-700 font-medium">{loc.building}</td>
                      <td className="px-6 py-3.5 text-gray-600">{loc.floor || "—"}</td>
                      <td className="px-6 py-3.5 text-gray-600">{loc.room || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

