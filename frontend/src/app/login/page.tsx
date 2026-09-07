"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { UserRole } from "@/lib/types";
import {
  Building2,
  Lock,
  Mail,
  GraduationCap,
  Wrench,
  Building,
  Shield,
  ArrowRight,
  AlertCircle,
} from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, demoLogin } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoLogin = async (role: UserRole) => {
    setError(null);
    setLoading(true);
    try {
      await demoLogin(role);
      router.push("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to demo login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto py-8 sm:py-12 space-y-8">
      {/* Brand Header */}
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-600 to-blue-700 flex items-center justify-center text-white shadow-xl shadow-indigo-500/30 mx-auto">
          <Building2 className="w-6 h-6" />
        </div>
        <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">
          Sign In to CampusPulse
        </h1>
        <p className="text-xs text-gray-500">
          Student Institutional Issues Reporting & Resolution Platform
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-center gap-3 text-xs text-rose-700 font-medium">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* 1-Click Evaluation Persona Switcher */}
      <div className="bg-white rounded-3xl border border-indigo-100 shadow-xl shadow-indigo-500/5 p-6 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-gray-100">
          <span className="text-xs font-bold uppercase tracking-wider text-indigo-900">
            1-Click Demo Evaluation Personas
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2.5">
          <button
            type="button"
            onClick={() => handleQuickDemoLogin("student")}
            disabled={loading}
            className="flex items-center gap-2 p-3 rounded-2xl border border-emerald-200 bg-emerald-50/60 hover:bg-emerald-100/60 text-emerald-900 text-xs font-semibold transition-all text-left"
          >
            <GraduationCap className="w-4 h-4 text-emerald-600 shrink-0" />
            <div>
              <div className="leading-tight">Aarav Sharma</div>
              <div className="text-[10px] text-emerald-700 font-normal">Student</div>
            </div>
          </button>

          <button
            type="button"
            onClick={() => handleQuickDemoLogin("handler")}
            disabled={loading}
            className="flex items-center gap-2 p-3 rounded-2xl border border-blue-200 bg-blue-50/60 hover:bg-blue-100/60 text-blue-900 text-xs font-semibold transition-all text-left"
          >
            <Wrench className="w-4 h-4 text-blue-600 shrink-0" />
            <div>
              <div className="leading-tight">Rajesh Sharma</div>
              <div className="text-[10px] text-blue-700 font-normal">Facilities Staff</div>
            </div>
          </button>

          <button
            type="button"
            onClick={() => handleQuickDemoLogin("higher_authority")}
            disabled={loading}
            className="flex items-center gap-2 p-3 rounded-2xl border border-purple-200 bg-purple-50/60 hover:bg-purple-100/60 text-purple-900 text-xs font-semibold transition-all text-left"
          >
            <Building className="w-4 h-4 text-purple-600 shrink-0" />
            <div>
              <div className="leading-tight">Dr. K. Verma</div>
              <div className="text-[10px] text-purple-700 font-normal">Dean of Infra</div>
            </div>
          </button>

          <button
            type="button"
            onClick={() => handleQuickDemoLogin("admin")}
            disabled={loading}
            className="flex items-center gap-2 p-3 rounded-2xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-900 text-xs font-semibold transition-all text-left"
          >
            <Shield className="w-4 h-4 text-slate-600 shrink-0" />
            <div>
              <div className="leading-tight">Administrator</div>
              <div className="text-[10px] text-slate-600 font-normal">Platform Admin</div>
            </div>
          </button>
        </div>
      </div>

      {/* Manual Login Form */}
      <form onSubmit={handleManualLogin} className="bg-white rounded-3xl border border-gray-200/90 shadow-sm p-6 space-y-4">
        <div className="text-xs font-bold uppercase tracking-wider text-gray-400 pb-2 border-b border-gray-100">
          Or Enter Credentials
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">Email Address</label>
          <div className="relative">
            <Mail className="w-4 h-4 text-gray-400 absolute left-3.5 top-3" />
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="student.aarav@campus.edu"
              className="w-full text-xs pl-10 pr-3 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">Password</label>
          <div className="relative">
            <Lock className="w-4 h-4 text-gray-400 absolute left-3.5 top-3" />
            <input
              required
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full text-xs pl-10 pr-3 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <span>{loading ? "Signing In..." : "Sign In"}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}

