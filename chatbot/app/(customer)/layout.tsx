"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Compass,
  MessageSquare,
  User,
  LogOut,
  ExternalLink,
  Loader2
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { ADMIN_LOGIN_URL } from "@/lib/env";

const navigationItems = [
  { name: "AI Assistant", href: "/ai-assistant", icon: MessageSquare },
];

export default function CustomerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);

  useEffect(() => {
    let isMounted = true;
    const checkAuth = async () => {
      try {
        const res = await apiClient.getCustomerMe();
        if (res && res.authenticated) {
          if (isMounted) {
            setIsAuthenticated(true);
            setCurrentUser(res.user);
          }
        } else {
          throw new Error("Unauthenticated");
        }
      } catch (err) {
        if (isMounted) {
          setIsAuthenticated(false);
          // Read the live location instead of depending on `pathname`, so this
          // effect runs once per mount: re-running it on every navigation
          // flipped `isAuthenticated` back to null and unmounted the whole
          // tree (wiping an in-progress chat) on any nav click.
          const currentPath =
            typeof window !== "undefined"
              ? `${window.location.pathname}${window.location.search}`
              : "/ai-assistant";
          const nextUrl = encodeURIComponent(currentPath);
          router.replace(`/login?next=${nextUrl}`);
        }
      }
    };

    checkAuth();
    return () => {
      isMounted = false;
    };
  }, [router]);

  const handleLogout = async () => {
    await apiClient.customerLogout();
    window.location.href = "/login";
  };

  // 1. Loading State - Do NOT render chatbot or protected UI until auth check completes
  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-500 to-blue-600 flex items-center justify-center shadow-xl shadow-sky-500/30 animate-pulse">
          <Compass className="w-7 h-7 text-white" />
        </div>
        <div className="flex items-center space-x-2 text-sm text-slate-400">
          <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
          <span>Verifying Customer Authentication...</span>
        </div>
      </div>
    );
  }

  // 2. Unauthenticated State - Render nothing (redirect is in progress)
  if (!isAuthenticated) {
    return null;
  }

  // 3. Authenticated State - Render Minimal Customer Layout & Protected Children
  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
      {/* Customer Minimal Header */}
      <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center space-x-3">
            <Link href="/ai-assistant" className="flex items-center space-x-2.5 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-blue-600 flex items-center justify-center shadow-md shadow-sky-500/20 group-hover:scale-105 transition-transform">
                <Compass className="w-6 h-6 text-white" />
              </div>
              <div>
                <span className="font-bold text-lg tracking-tight text-white block leading-tight">Travelogix</span>
                <span className="text-[10px] text-sky-400 font-medium tracking-wider uppercase block">Customer Portal</span>
              </div>
            </Link>
          </div>

          {/* Minimal Navigation */}
          <nav className="hidden md:flex items-center space-x-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-sky-500/10 text-sky-400 border border-sky-500/30"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* User Profile & Logout */}
          <div className="flex items-center space-x-3">
            <Link
              href="/profile"
              className="flex items-center space-x-2 text-xs text-slate-300 hover:text-white px-2.5 py-1.5 rounded-lg hover:bg-slate-800/70 transition-colors"
            >
              <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-sky-400 font-semibold">
                <User className="w-3.5 h-3.5" />
              </div>
              <span className="hidden sm:inline font-medium">
                {currentUser?.name || currentUser?.email || "Customer"}
              </span>
            </Link>

            <button
              onClick={handleLogout}
              title="Sign Out"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800/70 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Protected Content Area */}
      <main className="flex-1 flex flex-col">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/40 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <p>Travelogix AI Assistant &bull; Integrated Travel &amp; Logistics Platform</p>
          <a
            href={ADMIN_LOGIN_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] text-slate-500 hover:text-slate-300 transition-colors underline decoration-slate-700 inline-flex items-center gap-1"
          >
            <span>Admin Portal</span>
            <ExternalLink className="w-3 h-3 text-slate-500" />
          </a>
        </div>
      </footer>
    </div>
  );
}
