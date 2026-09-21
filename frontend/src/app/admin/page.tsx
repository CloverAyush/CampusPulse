"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Route, Sparkles, Trash2, UserPlus } from "lucide-react";

import { IssueCard } from "@/components/IssueCard";
import { EmptyState, ErrorState, InlineError, LoadingState } from "@/components/States";
import { api, errorMessage } from "@/lib/api";
import { Issue, IssueType, Location, RoutingPreview, RoutingRule, UserPublic, UserRole } from "@/lib/types";

type Tab = "routing" | "triage" | "taxonomy" | "people";

const TABS: { id: Tab; label: string }[] = [
  { id: "routing", label: "Routing rules" },
  { id: "triage", label: "Triage queue" },
  { id: "taxonomy", label: "Types & locations" },
  { id: "people", label: "Staff accounts" },
];

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("routing");
  const [rules, setRules] = useState<RoutingRule[]>([]);
  const [issueTypes, setIssueTypes] = useState<IssueType[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [handlers, setHandlers] = useState<UserPublic[]>([]);
  const [triage, setTriage] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [newRule, setNewRule] = useState({ issue_type_id: "", location_id: "", handler_id: "", priority: "10" });
  const [preview, setPreview] = useState<RoutingPreview | null>(null);
  const [previewInput, setPreviewInput] = useState({ issue_type_id: "", location_id: "" });
  const [newType, setNewType] = useState({ category: "", sub_type: "", requires_verification: true });
  const [newLocation, setNewLocation] = useState({ name: "", code: "", building: "", parent_id: "" });
  const [newStaff, setNewStaff] = useState({ email: "", full_name: "", password: "", role: "handler" as UserRole, department: "" });

  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const [ruleList, typeList, locationList, handlerList, triageQueue] = await Promise.all([
          api.listRoutingRules(),
          api.listIssueTypes(true),
          api.listLocations(true),
          api.listHandlers(),
          api.getIssues({ scope: "triage", limit: 50 }),
        ]);
        if (cancelled) return;
        setRules(ruleList);
        setIssueTypes(typeList);
        setLocations(locationList);
        setHandlers(handlerList);
        setTriage(triageQueue.items);
        setError(null);
      } catch (cause) {
        if (!cancelled) setError(cause);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const refresh = useCallback(() => setReloadToken((token) => token + 1), []);

  const reload = useCallback(() => {
    setLoading(true);
    setReloadToken((token) => token + 1);
  }, []);

  const withFeedback = async (action: () => Promise<unknown>, successMessage: string) => {
    setActionError(null);
    setNotice(null);
    try {
      await action();
      setNotice(successMessage);
      refresh();
    } catch (cause) {
      setActionError(errorMessage(cause));
    }
  };

  if (loading) return <LoadingState label="Loading configuration" />;
  if (error) return <ErrorState error={error} onRetry={reload} />;

  const inputClass =
    "w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100";
  const labelClass = "mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500";

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Configuration</h1>
        <p className="mt-1 text-sm text-gray-500">
          Routing is entirely determined by these rules. Change a rule and every
          matching report from that moment on goes to the new handler.
        </p>
      </header>

      <div className="flex flex-wrap gap-1 rounded-full bg-gray-100 p-1" role="tablist">
        {TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={tab === item.id}
            onClick={() => setTab(item.id)}
            className={`rounded-full px-4 py-1.5 text-sm font-semibold transition ${
              tab === item.id ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-800"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      <InlineError message={actionError} />
      {notice ? (
        <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-800" role="status">
          {notice}
        </p>
      ) : null}

      {tab === "routing" ? (
        <div className="space-y-5">
          <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-gray-500">
              <Sparkles className="h-4 w-4" aria-hidden />
              Test a rule before students find the gap
            </h2>
            <div className="grid gap-3 sm:grid-cols-3">
              <select
                aria-label="Issue type to test"
                value={previewInput.issue_type_id}
                onChange={(event) => setPreviewInput((state) => ({ ...state, issue_type_id: event.target.value }))}
                className={inputClass}
              >
                <option value="">Issue type</option>
                {issueTypes.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.category} · {type.sub_type}
                  </option>
                ))}
              </select>
              <select
                aria-label="Location to test"
                value={previewInput.location_id}
                onChange={(event) => setPreviewInput((state) => ({ ...state, location_id: event.target.value }))}
                className={inputClass}
              >
                <option value="">Location</option>
                {locations.map((location) => (
                  <option key={location.id} value={location.id}>
                    {location.name}
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={!previewInput.issue_type_id || !previewInput.location_id}
                onClick={() =>
                  void (async () => {
                    setActionError(null);
                    try {
                      setPreview(
                        await api.previewRouting(Number(previewInput.issue_type_id), Number(previewInput.location_id))
                      );
                    } catch (cause) {
                      setActionError(errorMessage(cause));
                    }
                  })()
                }
                className="rounded-xl bg-gray-900 px-4 py-2 text-sm font-semibold text-white hover:bg-gray-800 disabled:opacity-40"
              >
                Preview
              </button>
            </div>
            {preview ? (
              <p className="mt-3 rounded-xl bg-gray-50 px-3 py-2 text-xs text-gray-700">
                Resolves to <span className="font-semibold">{preview.handler?.full_name ?? "nobody"}</span> via{" "}
                <span className="font-mono">{preview.match_kind}</span>
                {preview.matched_rule_id ? ` (rule #${preview.matched_rule_id})` : ""}.
              </p>
            ) : null}
          </section>

          <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-gray-500">
              <Route className="h-4 w-4" aria-hidden />
              Add a rule
            </h2>
            <div className="grid gap-3 sm:grid-cols-4">
              <select
                aria-label="Issue type"
                value={newRule.issue_type_id}
                onChange={(event) => setNewRule((state) => ({ ...state, issue_type_id: event.target.value }))}
                className={inputClass}
              >
                <option value="">Any issue type</option>
                {issueTypes.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.category} · {type.sub_type}
                  </option>
                ))}
              </select>
              <select
                aria-label="Location"
                value={newRule.location_id}
                onChange={(event) => setNewRule((state) => ({ ...state, location_id: event.target.value }))}
                className={inputClass}
              >
                <option value="">Any location</option>
                {locations.map((location) => (
                  <option key={location.id} value={location.id}>
                    {location.name}
                  </option>
                ))}
              </select>
              <select
                aria-label="Handler"
                value={newRule.handler_id}
                onChange={(event) => setNewRule((state) => ({ ...state, handler_id: event.target.value }))}
                className={inputClass}
              >
                <option value="">Select a handler</option>
                {handlers.map((handler) => (
                  <option key={handler.id} value={handler.id}>
                    {handler.full_name}
                  </option>
                ))}
              </select>
              <input
                aria-label="Priority"
                type="number"
                min={0}
                max={1000}
                value={newRule.priority}
                onChange={(event) => setNewRule((state) => ({ ...state, priority: event.target.value }))}
                className={inputClass}
              />
            </div>
            <p className="mt-2 text-[11px] text-gray-400">
              Leave both dropdowns on &ldquo;Any&rdquo; to set the catch-all handler for miscellaneous issues.
            </p>
            <button
              type="button"
              disabled={!newRule.handler_id}
              onClick={() =>
                void withFeedback(
                  () =>
                    api.createRoutingRule({
                      issue_type_id: newRule.issue_type_id ? Number(newRule.issue_type_id) : null,
                      location_id: newRule.location_id ? Number(newRule.location_id) : null,
                      handler_id: Number(newRule.handler_id),
                      priority: Number(newRule.priority) || 10,
                    }),
                  "Routing rule added."
                )
              }
              className="mt-3 rounded-full bg-indigo-600 px-5 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-40"
            >
              Add rule
            </button>
          </section>

          <section className="overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-sm">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 text-[11px] uppercase tracking-wider text-gray-500">
                <tr>
                  <th scope="col" className="px-4 py-2.5 font-bold">Issue type</th>
                  <th scope="col" className="px-4 py-2.5 font-bold">Location</th>
                  <th scope="col" className="px-4 py-2.5 font-bold">Handler</th>
                  <th scope="col" className="px-4 py-2.5 font-bold">Priority</th>
                  <th scope="col" className="px-4 py-2.5 font-bold"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rules.map((rule) => {
                  const isCatchAll = !rule.issue_type_id && !rule.location_id;
                  return (
                    <tr key={rule.id} className={isCatchAll ? "bg-amber-50/50" : undefined}>
                      <td className="px-4 py-2.5 text-gray-800">
                        {rule.issue_type ? `${rule.issue_type.category} · ${rule.issue_type.sub_type}` : "Any"}
                      </td>
                      <td className="px-4 py-2.5 text-gray-800">{rule.location?.name ?? "Any"}</td>
                      <td className="px-4 py-2.5 font-semibold text-gray-900">
                        {rule.handler?.full_name ?? "—"}
                        {isCatchAll ? (
                          <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800">
                            Miscellaneous catch-all
                          </span>
                        ) : null}
                      </td>
                      <td className="px-4 py-2.5 text-gray-600">{rule.priority}</td>
                      <td className="px-4 py-2.5 text-right">
                        <button
                          type="button"
                          aria-label={`Delete rule ${rule.id}`}
                          onClick={() => void withFeedback(() => api.deleteRoutingRule(rule.id), "Routing rule deleted.")}
                          className="rounded-full p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600"
                        >
                          <Trash2 className="h-3.5 w-3.5" aria-hidden />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </section>
        </div>
      ) : null}

      {tab === "triage" ? (
        triage.length === 0 ? (
          <EmptyState
            title="Nothing waiting for triage"
            hint="Reports land here only when no routing rule matches and no catch-all handler is configured."
          />
        ) : (
          <div className="grid gap-3">
            {triage.map((issue) => (
              <IssueCard key={issue.id} issue={issue} />
            ))}
          </div>
        )
      ) : null}

      {tab === "taxonomy" ? (
        <div className="grid gap-5 lg:grid-cols-2">
          <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-gray-500">Add an issue type</h2>
            <div className="space-y-3">
              <div>
                <label htmlFor="type-category" className={labelClass}>Category</label>
                <input id="type-category" value={newType.category} onChange={(event) => setNewType((s) => ({ ...s, category: event.target.value }))} className={inputClass} />
              </div>
              <div>
                <label htmlFor="type-sub" className={labelClass}>Sub-type</label>
                <input id="type-sub" value={newType.sub_type} onChange={(event) => setNewType((s) => ({ ...s, sub_type: event.target.value }))} className={inputClass} />
              </div>
              <label className="flex items-center gap-2 text-xs text-gray-600">
                <input
                  type="checkbox"
                  checked={newType.requires_verification}
                  onChange={(event) => setNewType((s) => ({ ...s, requires_verification: event.target.checked }))}
                  className="h-4 w-4 rounded border-gray-300"
                />
                Students must confirm the fix before it closes
              </label>
              <button
                type="button"
                disabled={!newType.category || !newType.sub_type}
                onClick={() => void withFeedback(() => api.createIssueType(newType), "Issue type added.")}
                className="rounded-full bg-indigo-600 px-5 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-40"
              >
                Add issue type
              </button>
            </div>
            <ul className="mt-4 max-h-64 space-y-1 overflow-y-auto border-t border-gray-100 pt-3 text-xs text-gray-600">
              {issueTypes.map((type) => (
                <li key={type.id} className="flex justify-between gap-2">
                  <span>{type.category} · {type.sub_type}</span>
                  {type.requires_verification ? <span className="text-[10px] text-gray-400">verified</span> : null}
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-gray-500">Add a location</h2>
            <div className="space-y-3">
              <div>
                <label htmlFor="loc-name" className={labelClass}>Name</label>
                <input id="loc-name" value={newLocation.name} onChange={(event) => setNewLocation((s) => ({ ...s, name: event.target.value }))} className={inputClass} />
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label htmlFor="loc-code" className={labelClass}>Code</label>
                  <input id="loc-code" value={newLocation.code} onChange={(event) => setNewLocation((s) => ({ ...s, code: event.target.value }))} className={inputClass} />
                </div>
                <div>
                  <label htmlFor="loc-building" className={labelClass}>Building</label>
                  <input id="loc-building" value={newLocation.building} onChange={(event) => setNewLocation((s) => ({ ...s, building: event.target.value }))} className={inputClass} />
                </div>
              </div>
              <div>
                <label htmlFor="loc-parent" className={labelClass}>Sits inside</label>
                <select id="loc-parent" value={newLocation.parent_id} onChange={(event) => setNewLocation((s) => ({ ...s, parent_id: event.target.value }))} className={inputClass}>
                  <option value="">Nothing (top level)</option>
                  {locations.map((location) => (
                    <option key={location.id} value={location.id}>{location.name}</option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                disabled={!newLocation.name || !newLocation.code || !newLocation.building}
                onClick={() =>
                  void withFeedback(
                    () =>
                      api.createLocation({
                        name: newLocation.name,
                        code: newLocation.code,
                        building: newLocation.building,
                        parent_id: newLocation.parent_id ? Number(newLocation.parent_id) : null,
                      }),
                    "Location added."
                  )
                }
                className="rounded-full bg-indigo-600 px-5 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-40"
              >
                Add location
              </button>
            </div>
          </section>
        </div>
      ) : null}

      {tab === "people" ? (
        <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-gray-500">
            <UserPlus className="h-4 w-4" aria-hidden />
            Create a staff account
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label htmlFor="staff-name" className={labelClass}>Full name</label>
              <input id="staff-name" value={newStaff.full_name} onChange={(event) => setNewStaff((s) => ({ ...s, full_name: event.target.value }))} className={inputClass} />
            </div>
            <div>
              <label htmlFor="staff-email" className={labelClass}>Email</label>
              <input id="staff-email" type="email" value={newStaff.email} onChange={(event) => setNewStaff((s) => ({ ...s, email: event.target.value }))} className={inputClass} />
            </div>
            <div>
              <label htmlFor="staff-password" className={labelClass}>Temporary password</label>
              <input id="staff-password" type="text" value={newStaff.password} onChange={(event) => setNewStaff((s) => ({ ...s, password: event.target.value }))} className={inputClass} />
              <p className="mt-1 text-[11px] text-gray-400">At least 10 characters with a letter and a number. Ask them to change it.</p>
            </div>
            <div>
              <label htmlFor="staff-role" className={labelClass}>Role</label>
              <select id="staff-role" value={newStaff.role} onChange={(event) => setNewStaff((s) => ({ ...s, role: event.target.value as UserRole }))} className={inputClass}>
                <option value="handler">Handler</option>
                <option value="higher_authority">Higher authority</option>
                <option value="admin">Administrator</option>
              </select>
            </div>
          </div>
          <button
            type="button"
            disabled={!newStaff.email || !newStaff.full_name || newStaff.password.length < 10}
            onClick={() =>
              void withFeedback(async () => {
                await api.createStaffUser({
                  email: newStaff.email,
                  full_name: newStaff.full_name,
                  password: newStaff.password,
                  role: newStaff.role,
                  department: newStaff.department || undefined,
                });
                setNewStaff({ email: "", full_name: "", password: "", role: "handler", department: "" });
              }, "Staff account created.")
            }
            className="mt-3 rounded-full bg-indigo-600 px-5 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-40"
          >
            Create account
          </button>

          <ul className="mt-5 divide-y divide-gray-100 border-t border-gray-100 pt-3 text-xs">
            {handlers.map((handler) => (
              <li key={handler.id} className="flex justify-between py-2">
                <span className="font-semibold text-gray-800">{handler.full_name}</span>
                <span className="text-gray-400">{handler.role.replace("_", " ")}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
