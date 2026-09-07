"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Notification } from "@/lib/types";
import {
  Building2,
  PlusCircle,
  FileText,
  Wrench,
  ShieldAlert,
  Settings,
  Bell,
  CheckCheck,
  LogOut,
  Menu,
  X,
} from "lucide-react";

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifs, setShowNotifs] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const fetchNotifs = async () => {
    if (user) {
      try {
        const notifs = await api.getNotifications();
        setNotifications(notifs);
      } catch {
        // ignore notification fetch failure in background
      }
    }
  };

  useEffect(() => {
    fetchNotifs();
    const interval = setInterval(fetchNotifs, 10000);
    return () => clearInterval(interval);
  }, [user]);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {
      // ignore
    }
  };

  const navLinks = [
    {
      href: "/report",
      label: "Report Issue",
      icon: <PlusCircle className="w-4 h-4" />,
      roles: ["student", "admin"],
      primary: true,
    },
    {
      href: "/my-reports",
      label: "My Reports & Issues",
      icon: <FileText className="w-4 h-4" />,
      roles: ["student", "admin"],
    },
    {
      href: "/handler",
      label: "Handler Queue",
      icon: <Wrench className="w-4 h-4" />,
      roles: ["handler", "admin"],
    },
    {
      href: "/higher-authority",
      label: "Escalated Cases",
      icon: <ShieldAlert className="w-4 h-4" />,
      roles: ["higher_authority", "admin"],
    },
    {
      href: "/admin",
      label: "Admin Config",
      icon: <Settings className="w-4 h-4" />,
      roles: ["admin"],
    },
  ];

  const visibleLinks = navLinks.filter(
    (link) => !user || link.roles.includes(user.role)
  );

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-blue-700 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <span className="text-lg font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  Campus<span className="text-indigo-600">Pulse</span>
                </span>
                <span className="block text-[10px] uppercase tracking-wider font-semibold text-gray-500">
                  Resolution Platform
                </span>
              </div>
            </Link>

            {/* Desktop Navigation Links */}
            <div className="hidden md:flex items-center space-x-1 pl-4 border-l border-gray-200">
              {visibleLinks.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                      link.primary
                        ? "bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm shadow-indigo-500/20"
                        : isActive
                        ? "bg-indigo-50 text-indigo-700 font-semibold"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                    }`}
                  >
                    {link.icon}
                    <span>{link.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Right Action Items */}
          <div className="flex items-center gap-3">
            {/* Notification Bell */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowNotifs(!showNotifs)}
                className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg focus:outline-none transition-colors"
                aria-label="Notifications"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white ring-2 ring-white">
                    {unreadCount}
                  </span>
                )}
              </button>

              {showNotifs && (
                <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-gray-100 py-3 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="flex items-center justify-between px-4 pb-2 border-b border-gray-100">
                    <div className="font-semibold text-sm text-gray-900 flex items-center gap-2">
                      <span>In-App Notifications</span>
                      {unreadCount > 0 && (
                        <span className="text-xs bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full font-bold">
                          {unreadCount} new
                        </span>
                      )}
                    </div>
                    {unreadCount > 0 && (
                      <button
                        onClick={handleMarkAllRead}
                        className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1 font-medium"
                      >
                        <CheckCheck className="w-3.5 h-3.5" />
                        Mark all read
                      </button>
                    )}
                  </div>

                  <div className="max-h-80 overflow-y-auto divide-y divide-gray-50">
                    {notifications.length === 0 ? (
                      <div className="py-8 text-center text-xs text-gray-400">
                        No notifications yet.
                      </div>
                    ) : (
                      notifications.slice(0, 15).map((n) => (
                        <div
                          key={n.id}
                          className={`p-3.5 text-xs transition-colors hover:bg-gray-50 ${
                            !n.is_read ? "bg-indigo-50/50" : ""
                          }`}
                        >
                          <div className="font-semibold text-gray-900 mb-0.5 flex items-center justify-between">
                            <span>{n.title}</span>
                            <span className="text-[10px] font-normal text-gray-400">
                              {new Date(n.created_at).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                          </div>
                          <p className="text-gray-600 text-xs leading-relaxed">{n.message}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* User Profile Pill */}
            {user && (
              <div className="hidden sm:flex items-center gap-2 pl-2 border-l border-gray-200">
                <div className="text-right">
                  <div className="text-xs font-semibold text-gray-900 leading-tight">
                    {user.full_name}
                  </div>
                  <div className="text-[10px] text-gray-500 capitalize">{user.role.replace("_", " ")}</div>
                </div>
              </div>
            )}

            {/* Logout */}
            <button
              onClick={logout}
              title="Sign Out"
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white px-4 pt-2 pb-4 space-y-1">
          {visibleLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium ${
                pathname === link.href
                  ? "bg-indigo-50 text-indigo-700 font-semibold"
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              {link.icon}
              <span>{link.label}</span>
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
};

