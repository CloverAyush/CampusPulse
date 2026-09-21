"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell,
  Building2,
  FileText,
  LayoutGrid,
  LogOut,
  Menu,
  PlusCircle,
  Settings,
  Wrench,
  X,
} from "lucide-react";

import { api } from "@/lib/api";
import { ROLE_LABELS, useAuth } from "@/lib/auth";
import { formatRelative } from "@/lib/format";
import { Notification, UserRole } from "@/lib/types";

const POLL_INTERVAL_MS = 30000;
const MAX_BACKOFF_MS = 300000;

interface NavLink {
  href: string;
  label: string;
  icon: React.ReactNode;
  roles: UserRole[];
  primary?: boolean;
}

const NAV_LINKS: NavLink[] = [
  { href: "/report", label: "Report an issue", icon: <PlusCircle className="h-4 w-4" aria-hidden />, roles: ["student", "admin"], primary: true },
  { href: "/my-reports", label: "Issues", icon: <FileText className="h-4 w-4" aria-hidden />, roles: ["student", "admin"] },
  { href: "/handler", label: "My queue", icon: <Wrench className="h-4 w-4" aria-hidden />, roles: ["handler"] },
  { href: "/higher-authority", label: "Escalations", icon: <Building2 className="h-4 w-4" aria-hidden />, roles: ["higher_authority", "admin"] },
  { href: "/admin", label: "Configuration", icon: <Settings className="h-4 w-4" aria-hidden />, roles: ["admin"] },
];

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [inbox, setInbox] = useState<{ ownerId: number; items: Notification[] }>({
    ownerId: -1,
    items: [],
  });
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const backoffRef = useRef(POLL_INTERVAL_MS);
  const panelRef = useRef<HTMLDivElement | null>(null);

  const closeMenus = useCallback(() => {
    setMobileMenuOpen(false);
    setNotificationsOpen(false);
  }, []);

  const userId = user?.id ?? null;

  useEffect(() => {
    if (userId === null) return;

    let timer: ReturnType<typeof setTimeout>;
    let cancelled = false;

    const poll = async () => {
      try {
        const page = await api.getNotifications();
        if (cancelled) return;
        setInbox({ ownerId: userId, items: page.items });
        backoffRef.current = POLL_INTERVAL_MS;
      } catch {
        // Background polling must not interrupt the page. Back off instead, so an
        // outage does not turn every open tab into a request storm.
        backoffRef.current = Math.min(backoffRef.current * 2, MAX_BACKOFF_MS);
      }
    };

    const schedule = () => {
      timer = setTimeout(async () => {
        if (cancelled) return;
        if (document.visibilityState === "visible") await poll();
        schedule();
      }, backoffRef.current);
    };

    void poll();
    schedule();

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [userId]);

  useEffect(() => {
    if (!notificationsOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setNotificationsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [notificationsOpen]);

  if (!user) return null;

  // A stale inbox from a previously signed-in account must never render, so the
  // list is only shown when it was fetched for the user who is signed in now.
  const notifications = inbox.ownerId === user.id ? inbox.items : [];
  const unreadCount = notifications.filter((item) => !item.is_read).length;
  const visibleLinks = NAV_LINKS.filter((link) => link.roles.includes(user.role));

  const handleMarkAllRead = async () => {
    const previous = inbox;
    setInbox((state) => ({
      ...state,
      items: state.items.map((item) => ({ ...item, is_read: true })),
    }));
    try {
      await api.markAllNotificationsRead();
    } catch {
      setInbox(previous);
    }
  };

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white/90 backdrop-blur">
      <nav className="mx-auto flex h-14 max-w-7xl items-center gap-3 px-4 sm:px-6 lg:px-8" aria-label="Main">
        <Link href="/" className="flex shrink-0 items-center gap-2 font-bold tracking-tight text-gray-900">
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-indigo-600 text-white">
            <LayoutGrid className="h-4 w-4" aria-hidden />
          </span>
          CampusPulse
        </Link>

        <div className="ml-2 hidden flex-1 items-center gap-1 md:flex">
          {visibleLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={closeMenus}
                aria-current={isActive ? "page" : undefined}
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition ${
                  isActive
                    ? "bg-indigo-50 text-indigo-700"
                    : link.primary
                      ? "bg-indigo-600 text-white hover:bg-indigo-700"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
              >
                {link.icon}
                {link.label}
              </Link>
            );
          })}
        </div>

        <div className="ml-auto flex items-center gap-1.5">
          <div className="relative" ref={panelRef}>
            <button
              type="button"
              onClick={() => setNotificationsOpen((open) => !open)}
              aria-label={unreadCount > 0 ? `Notifications, ${unreadCount} unread` : "Notifications"}
              aria-expanded={notificationsOpen}
              className="relative grid h-9 w-9 place-items-center rounded-full text-gray-600 hover:bg-gray-100"
            >
              <Bell className="h-4.5 w-4.5" aria-hidden />
              {unreadCount > 0 ? (
                <span className="absolute right-1 top-1 grid h-4 min-w-4 place-items-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              ) : null}
            </button>

            {notificationsOpen ? (
              <div className="absolute right-0 mt-2 w-80 max-w-[calc(100vw-2rem)] overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-xl">
                <div className="flex items-center justify-between border-b border-gray-100 px-4 py-2.5">
                  <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Notifications</p>
                  {unreadCount > 0 ? (
                    <button type="button" onClick={handleMarkAllRead} className="text-xs font-semibold text-indigo-600 hover:underline">
                      Mark all read
                    </button>
                  ) : null}
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <p className="px-4 py-8 text-center text-xs text-gray-400">Nothing yet.</p>
                  ) : (
                    notifications.map((item) => (
                      <article
                        key={item.id}
                        className={`border-b border-gray-50 px-4 py-2.5 last:border-0 ${item.is_read ? "" : "bg-indigo-50/50"}`}
                      >
                        <p className="text-xs font-semibold text-gray-900">{item.title}</p>
                        <p className="mt-0.5 text-xs leading-relaxed text-gray-600">{item.message}</p>
                        <p className="mt-1 text-[10px] text-gray-400">{formatRelative(item.created_at)}</p>
                      </article>
                    ))
                  )}
                </div>
              </div>
            ) : null}
          </div>

          <div className="hidden items-center gap-2 rounded-full border border-gray-200 py-1 pl-3 pr-1 sm:flex">
            <div className="text-right leading-tight">
              <p className="text-xs font-semibold text-gray-900">{user.full_name}</p>
              <p className="text-[10px] text-gray-500">{ROLE_LABELS[user.role]}</p>
            </div>
            <button
              type="button"
              onClick={logout}
              aria-label="Sign out"
              className="grid h-7 w-7 place-items-center rounded-full text-gray-500 hover:bg-gray-100 hover:text-gray-900"
            >
              <LogOut className="h-4 w-4" aria-hidden />
            </button>
          </div>

          <button
            type="button"
            onClick={() => setMobileMenuOpen((open) => !open)}
            aria-label="Menu"
            aria-expanded={mobileMenuOpen}
            className="grid h-9 w-9 place-items-center rounded-full text-gray-600 hover:bg-gray-100 md:hidden"
          >
            {mobileMenuOpen ? <X className="h-4.5 w-4.5" aria-hidden /> : <Menu className="h-4.5 w-4.5" aria-hidden />}
          </button>
        </div>
      </nav>

      {mobileMenuOpen ? (
        <div className="border-t border-gray-100 px-4 py-2 md:hidden">
          {visibleLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={closeMenus}
              className="flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              {link.icon}
              {link.label}
            </Link>
          ))}
          <button
            type="button"
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <LogOut className="h-4 w-4" aria-hidden />
            Sign out ({user.full_name})
          </button>
        </div>
      ) : null}
    </header>
  );
};
