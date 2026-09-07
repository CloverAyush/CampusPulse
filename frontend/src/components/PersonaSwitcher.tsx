"use client";

import React, { useState } from "react";
import { useAuth } from "@/lib/auth";
import { UserRole } from "@/lib/types";
import { Users, Shield, Wrench, GraduationCap, Building2, ChevronDown, Check } from "lucide-react";

export const PersonaSwitcher: React.FC = () => {
  const { user, demoLogin, loading } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  const personas: { role: UserRole; name: string; title: string; icon: React.ReactNode; color: string }[] = [
    {
      role: "student",
      name: "Aarav Sharma",
      title: "Student (Computer Science)",
      icon: <GraduationCap className="w-4 h-4 text-emerald-600" />,
      color: "border-emerald-200 bg-emerald-50 text-emerald-900",
    },
    {
      role: "handler",
      name: "Rajesh Sharma",
      title: "Facilities & Electrical Handler",
      icon: <Wrench className="w-4 h-4 text-blue-600" />,
      color: "border-blue-200 bg-blue-50 text-blue-900",
    },
    {
      role: "higher_authority",
      name: "Dr. K. Verma",
      title: "Dean of Campus Infrastructure",
      icon: <Building2 className="w-4 h-4 text-purple-600" />,
      color: "border-purple-200 bg-purple-50 text-purple-900",
    },
    {
      role: "admin",
      name: "Administrator",
      title: "CampusPulse Admin",
      icon: <Shield className="w-4 h-4 text-slate-600" />,
      color: "border-slate-200 bg-slate-50 text-slate-900",
    },
  ];

  const currentPersona = personas.find((p) => p.role === user?.role) || personas[0];

  const handleSelectRole = async (role: UserRole) => {
    setIsOpen(false);
    await demoLogin(role);
  };

  return (
    <div className="relative z-50">
      <div className="bg-gradient-to-r from-indigo-900 via-slate-900 to-indigo-950 text-white px-4 py-1.5 text-xs flex flex-wrap items-center justify-between gap-2 border-b border-indigo-800/40">
        <div className="flex items-center gap-2">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="font-semibold tracking-wide text-indigo-200">DEMO EVALUATION PERSONA:</span>
          <div className="flex items-center gap-1.5 font-medium bg-white/10 px-2 py-0.5 rounded-full border border-white/10">
            {currentPersona.icon}
            <span className="text-white">{user?.full_name || currentPersona.name}</span>
            <span className="text-indigo-300">({user?.role || currentPersona.role})</span>
          </div>
        </div>

        <div className="relative">
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-md transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          >
            <Users className="w-3.5 h-3.5" />
            <span>Switch Persona</span>
            <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isOpen ? "rotate-180" : ""}`} />
          </button>

          {isOpen && (
            <div className="absolute right-0 mt-2 w-72 bg-white rounded-xl shadow-2xl border border-gray-100 py-2 z-50 text-gray-800 animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="px-3 py-1.5 text-[11px] font-semibold text-gray-400 uppercase tracking-wider border-b border-gray-100">
                Switch Active Role
              </div>
              <div className="p-1 space-y-1">
                {personas.map((p) => {
                  const isSelected = user?.role === p.role;
                  return (
                    <button
                      key={p.role}
                      type="button"
                      onClick={() => handleSelectRole(p.role)}
                      className={`w-full text-left px-3 py-2 rounded-lg flex items-center justify-between transition-all ${
                        isSelected
                          ? "bg-indigo-50 text-indigo-900 font-medium"
                          : "hover:bg-gray-50 text-gray-700"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <div className="p-1.5 rounded-md bg-gray-100">{p.icon}</div>
                        <div>
                          <div className="text-xs font-semibold text-gray-900">{p.name}</div>
                          <div className="text-[11px] text-gray-500">{p.title}</div>
                        </div>
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-indigo-600" />}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

