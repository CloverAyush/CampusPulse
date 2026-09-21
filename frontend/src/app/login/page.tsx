"use client";

import React, { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { LayoutGrid, Loader2 } from "lucide-react";

import { InlineError } from "@/components/States";
import { errorMessage } from "@/lib/api";
import { ROLE_HOME, useAuth } from "@/lib/auth";

type Mode = "signin" | "register";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, status, login, register } = useAuth();

  const [mode, setMode] = useState<Mode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [department, setDepartment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const nextPath = searchParams.get("next");
  const sessionExpired = searchParams.get("expired") === "1";

  useEffect(() => {
    if (status === "authenticated" && user) {
      router.replace(nextPath && nextPath.startsWith("/") ? nextPath : ROLE_HOME[user.role]);
    }
  }, [status, user, nextPath, router]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const signedIn =
        mode === "signin"
          ? await login(email.trim(), password)
          : await register({
              email: email.trim(),
              password,
              full_name: fullName.trim(),
              department: department.trim() || undefined,
            });
      router.replace(nextPath && nextPath.startsWith("/") ? nextPath : ROLE_HOME[signedIn.role]);
    } catch (cause) {
      setError(errorMessage(cause));
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-md flex-col justify-center py-10">
      <div className="mb-6 text-center">
        <span className="mx-auto mb-3 grid h-11 w-11 place-items-center rounded-2xl bg-indigo-600 text-white">
          <LayoutGrid className="h-5 w-5" aria-hidden />
        </span>
        <h1 className="text-2xl font-bold tracking-tight">CampusPulse</h1>
        <p className="mt-1 text-sm text-gray-500">
          Report shared campus problems and follow them through to a verified fix.
        </p>
      </div>

      {sessionExpired ? (
        <p className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800" role="status">
          Your session expired. Sign in again to continue.
        </p>
      ) : null}

      <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-5 grid grid-cols-2 gap-1 rounded-full bg-gray-100 p-1" role="tablist">
          {(["signin", "register"] as Mode[]).map((option) => (
            <button
              key={option}
              type="button"
              role="tab"
              aria-selected={mode === option}
              onClick={() => {
                setMode(option);
                setError(null);
              }}
              className={`rounded-full py-1.5 text-sm font-semibold transition ${
                mode === option ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-800"
              }`}
            >
              {option === "signin" ? "Sign in" : "Create account"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          {mode === "register" ? (
            <>
              <div>
                <label htmlFor="full_name" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
                  Full name
                </label>
                <input
                  id="full_name"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  required
                  minLength={2}
                  autoComplete="name"
                  className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                />
              </div>
              <div>
                <label htmlFor="department" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
                  Department <span className="font-medium normal-case text-gray-400">(optional)</span>
                </label>
                <input
                  id="department"
                  value={department}
                  onChange={(event) => setDepartment(event.target.value)}
                  autoComplete="organization"
                  className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                />
              </div>
            </>
          ) : null}

          <div>
            <label htmlFor="email" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
              College email
            </label>
            <input
              id="email"
              type="email"
              inputMode="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoComplete="email"
              className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1 block text-xs font-bold uppercase tracking-wider text-gray-500">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              minLength={mode === "register" ? 10 : 1}
              autoComplete={mode === "register" ? "new-password" : "current-password"}
              className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
            {mode === "register" ? (
              <p className="mt-1 text-[11px] text-gray-400">
                At least 10 characters, including a letter and a number.
              </p>
            ) : null}
          </div>

          <InlineError message={error} />

          <button
            type="submit"
            disabled={submitting}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-indigo-600 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : null}
            {mode === "signin" ? "Sign in" : "Create student account"}
          </button>
        </form>

        {mode === "register" ? (
          <p className="mt-4 text-center text-[11px] leading-relaxed text-gray-400">
            Accounts created here are student accounts. Handler and administrator
            accounts are created by your campus administrator.
          </p>
        ) : null}
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}
