"use client";

import { useState, useEffect, useCallback } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  LayoutDashboard,
  Bot,
  FileText,
  Settings,
  LogOut,
  Menu,
  X,
  Play,
  CreditCard,
  Shield,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/agents", label: "Agents", icon: Bot },
  { href: "/dashboard/credit", label: "Credit", icon: CreditCard },
  { href: "/dashboard/audit", label: "Audit Logs", icon: FileText },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const closeMobile = useCallback(() => setMobileOpen(false), []);

  useEffect(() => {
    if (!mobileOpen) return;
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeMobile();
    };
    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [mobileOpen, closeMobile]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  };

  const navContent = (
    <>
      <div className="px-5 py-5">
        <h1 className="text-base font-medium text-text-primary">TrustPay</h1>
      </div>

      <nav className="flex-1 px-3 space-y-0.5" role="navigation" aria-label="Main navigation">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={closeMobile}
              aria-current={isActive ? "page" : undefined}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? "bg-surface-warm text-text-primary"
                  : "text-text-muted hover:text-text-primary hover:bg-surface-warm"
              }`}
            >
              <Icon size={16} strokeWidth={1.5} aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="px-3 py-4 border-t border-border-cool">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-surface-warm flex items-center justify-center text-text-secondary text-sm font-medium" aria-hidden="true">
            O
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-text-primary truncate">Owner</p>
            <p className="text-xs text-text-muted">Admin</p>
          </div>
          <button
            onClick={handleLogout}
            className="text-text-muted hover:text-danger transition-colors cursor-pointer"
            aria-label="Logout"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </>
  );

  return (
    <>
      <button
        className="fixed top-4 left-4 z-50 md:hidden bg-canvas border border-border-warm rounded-[6px] p-2 text-text-secondary hover:text-text-primary transition-colors cursor-pointer"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label={mobileOpen ? "Close menu" : "Open menu"}
        aria-expanded={mobileOpen}
      >
        {mobileOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          onClick={closeMobile}
          aria-hidden="true"
        />
      )}

      <aside className="hidden md:flex fixed left-0 top-0 bottom-0 w-60 bg-canvas border-r border-border-cool flex-col z-40">
        {navContent}
      </aside>

      <aside
        className={`fixed left-0 top-0 bottom-0 w-60 bg-canvas border-r border-border-cool flex flex-col z-50 md:hidden transition-transform duration-200 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {navContent}
      </aside>
    </>
  );
}
