import type { Metadata } from "next";

import "./globals.css";
import { AuthGate } from "@/components/AuthGate";
import { Navbar } from "@/components/Navbar";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "CampusPulse",
  description:
    "Report shared campus problems in seconds. Deterministic routing, evidence-backed resolution, student verification.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full bg-slate-50 antialiased">
      <body className="flex h-full flex-col font-sans text-gray-900 selection:bg-indigo-500 selection:text-white">
        <AuthProvider>
          <Navbar />
          <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
            <AuthGate>{children}</AuthGate>
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
