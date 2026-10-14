"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Package,
  Users,
  Truck,
  MapPin,
  MessageSquare,
  UserCheck,
  AlertTriangle,
  CheckCircle,
  FileText,
  ShieldAlert,
  LogOut,
  ShieldCheck,
  Loader2,
  Menu,
} from "lucide-react";
import { adminApiClient } from "@/lib/api-client";

/** Roles the admin console is willing to render. Mirrors the backend's ADMIN_ROLES. */
const ADMIN_ROLES = ["ADMIN", "LOGISTICS_ADMIN", "SUPERADMIN"];

const adminNavItems = [
  { name: "Dashboard", href: "/admin/dashboard", icon: LayoutDashboard },
  { name: "Shipments", href: "/admin/shipments", icon: Package },
  { name: "Drivers", href: "/admin/drivers", icon: Users },
  { name: "Vehicles", href: "/admin/vehicles", icon: Truck },
  { name: "Tracking", href: "/admin/tracking", icon: MapPin },
  { name: "Conversations", href: "/admin/conversations", icon: MessageSquare },
  { name: "Customers", href: "/admin/customers", icon: UserCheck },
  { name: "Delayed Shipments", href: "/admin/delayed-shipments", icon: AlertTriangle },
  { name: "Delivered", href: "/admin/delivered", icon: CheckCircle },
  { name: "Reports", href: "/admin/reports", icon: FileText },
  { name: "Audit Logs", href: "/admin/audit-logs", icon: ShieldAlert },
];

export default function AdminPortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [adminUser, setAdminUser] = useState<{ email?: string; role?: string } | null>(null);
  // The 256px sidebar leaves almost no room on a phone, so it becomes an
  // off-canvas drawer below lg.
  const [isSidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    // Guards against a resolved response updating an unmounted component
    // (the layout unmounts as soon as a redirect begins).
    let cancelled = false;

    const redirectToLogin = () => {
      if (cancelled) return;
      const currentPath = encodeURIComponent(pathname || "/admin/dashboard");
      window.location.href = `/admin/login?next=${currentPath}`;
    };

    const checkAuth = async () => {
      if (typeof window === "undefined") return;

      // Reset first: a stale `true` from a previous check must never keep the
      // console rendered while the new check is in flight.
      setIsAuthenticated(null);
      setAdminUser(null);

      try {
        // Session comes from the httpOnly `travelogix_admin_token` cookie.
        const data = await adminApiClient.get<any>("/auth/admin/me");
        if (cancelled) return;

        /**
         * `res.ok` alone is NOT proof of an admin session: /auth/admin/me
         * answers HTTP 200 with `{authenticated:false}` for an anonymous or
         * customer caller. Require an explicit authenticated flag AND an
         * administrative role, and never invent an identity when the payload
         * is thin.
         */
        const role = String(data?.user?.role || "").toUpperCase();
        const isAdmin = Boolean(
          data && data.authenticated === true && data.user && ADMIN_ROLES.includes(role)
        );

        if (!isAdmin) {
          setIsAuthenticated(false);
          setAdminUser(null);
          redirectToLogin();
          return;
        }

        setAdminUser(data.user);
        setIsAuthenticated(true);
      } catch (e) {
        if (cancelled) return;
        // No local credential to clear any more; the httpOnly cookie is only
        // removable by the backend (logout) or by the browser on expiry.
        setIsAuthenticated(false);
        setAdminUser(null);
        redirectToLogin();
      }
    };

    checkAuth();
    return () => {
      cancelled = true;
    };
  }, [pathname]);

  const handleLogout = async () => {
    try {
      await adminApiClient.post<any>("/auth/admin/logout");
    } catch (e) {
      // Handled silently: the redirect below still ends the local session.
    }
    setAdminUser(null);
    setIsAuthenticated(false);
    window.location.href = "/admin/login";
  };

  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="text-center space-y-3">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400 font-medium">Verifying Travelogix Admin Credentials...</p>
        </div>
      </div>
    );
  }

  // Rejected session: the redirect to /admin/login is already in flight. Render
  // nothing rather than the console shell for an unauthenticated caller.
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="text-center space-y-3">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400 font-medium">Redirecting to the admin sign-in page...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100 font-sans">
      {/* Mobile drawer backdrop */}
      {isSidebarOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-slate-950/70 lg:hidden"
        />
      )}

      {/* Admin Sidebar — off-canvas below lg, static from lg up */}
      <aside
        className={`w-64 border-r border-slate-800 bg-slate-900/90 flex flex-col shrink-0
          fixed inset-y-0 left-0 z-40 transition-transform duration-200 lg:static lg:translate-x-0
          ${isSidebarOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        {/* Brand */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800 space-x-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center shadow-md shadow-indigo-500/20">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-bold text-base tracking-tight text-white block">Travelogix</span>
            <span className="text-[10px] text-indigo-400 font-semibold uppercase tracking-wider block">Admin Console</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {adminNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-indigo-600/15 text-indigo-400 border border-indigo-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* User Footer */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2.5 min-w-0">
            <div className="w-7 h-7 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-semibold text-xs shrink-0">
              {(adminUser?.email || "A").charAt(0).toUpperCase()}
            </div>
            <div className="text-xs truncate">
              <p className="font-medium text-slate-200 truncate">{adminUser?.email || "Signed-in administrator"}</p>
              <p className="text-[10px] text-indigo-400 font-semibold">{adminUser?.role || "—"}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            title="Sign Out"
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors shrink-0"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-4 sm:px-8 flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <button
              type="button"
              onClick={() => setSidebarOpen((open) => !open)}
              aria-label="Toggle navigation"
              aria-expanded={isSidebarOpen}
              className="lg:hidden p-2 -ml-1 text-slate-300 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="text-xs text-slate-400 truncate">
              Operations Workspace &bull; <span className="text-slate-200 font-medium">India Hub</span>
            </div>
          </div>
          <div className="flex items-center space-x-3 text-xs">
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              FastAPI Connected
            </span>
          </div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
