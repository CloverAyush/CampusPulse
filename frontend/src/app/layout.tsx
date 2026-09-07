import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { Navbar } from "@/components/Navbar";
import { PersonaSwitcher } from "@/components/PersonaSwitcher";

export const metadata: Metadata = {
  title: "CampusPulse - Student Institutional Issues Platform",
  description: "Low-friction institutional reporting, deterministic routing, and verifiable issue resolution for campus infrastructure.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full bg-slate-50 antialiased">
      <body className="h-full flex flex-col font-sans text-gray-900 selection:bg-indigo-500 selection:text-white">
        <AuthProvider>
          <PersonaSwitcher />
          <Navbar />
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
