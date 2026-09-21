"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";

import { LoadingState } from "@/components/States";
import { ROLE_HOME, useAuth } from "@/lib/auth";

export default function HomePage() {
  const { user, status } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "authenticated" && user) {
      router.replace(ROLE_HOME[user.role]);
    }
  }, [status, user, router]);

  return <LoadingState label="Taking you to your dashboard" />;
}
