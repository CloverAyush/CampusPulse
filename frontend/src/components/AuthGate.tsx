"use client";

import React, { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { LoadingState } from "@/components/States";
import { useAuth } from "@/lib/auth";

const PUBLIC_ROUTES = new Set(["/login"]);

/** The only gate that matters is on the API, which authorises every request. This
 *  exists so an unauthenticated visitor sees the sign-in page instead of a page of
 *  failed requests. */
export const AuthGate: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { status } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = PUBLIC_ROUTES.has(pathname);

  useEffect(() => {
    if (status === "anonymous" && !isPublic) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [status, isPublic, pathname, router]);

  if (isPublic) return <>{children}</>;
  if (status !== "authenticated") return <LoadingState label="Checking your session" />;
  return <>{children}</>;
};
