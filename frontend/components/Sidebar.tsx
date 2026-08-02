"use client";

import { useState, useEffect, useCallback } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  LayoutDashboard,
  Bot,
  FileText,
  Settings,
  Shield,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { Badge } from "./ui/Badge";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/audit", label: "Audit Logs", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const closeMobile = useCallback(() => setMobileOpen(false), []);

  // Close on escape
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
      {/* Logo */}
      <div className="px-4 py-5 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan/20 flex items-center justify-center">
            <Shield size={18} className="text-cyan" />
          </div>
          <div>
            <h1 className="text-sm font-bold">AgentFinance</h1>
            <p className="text-xs text-text-muted">Control System</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1" role="navigation" aria-label="Main navigation">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={closeMobile}
              aria-current={isActive ? "page" : undefined}
              className={`flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors ${
                isActive
                  ? "bg-elevated text-cyan"
                  : "text-text-secondary hover:bg-elevated hover:text-text-primary"
              }`}
            >
              <Icon size={16} aria-hidden="true" />
              <span>{item.label}</span>
              {item.href === "/audit" && (
                <Badge variant="cyan" className="ml-auto text-[10px]">
                  Live
                </Badge>
              )}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="px-3 py-4 border-t border-border">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-purple/20 flex items-center justify-center text-purple text-sm font-medium" aria-hidden="true">
            O
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">Owner</p>
            <p className="text-xs text-text-muted">Admin</p>
          </div>
          <button
            onClick={handleLogout}
            className="text-text-muted hover:text-red transition-colors"
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
      {/* Mobile hamburger button */}
      <button
        className="fixed top-4 left-4 z-50 md:hidden bg-surface border border-border rounded-lg p-2 text-text-secondary hover:text-text-primary transition-colors"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label={mobileOpen ? "Close menu" : "Open menu"}
        aria-expanded={mobileOpen}
      >
        {mobileOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={closeMobile}
          aria-hidden="true"
        />
      )}

      {/* Desktop sidebar */}
      <aside className="hidden md:flex fixed left-0 top-0 bottom-0 w-60 bg-surface border-r border-border flex-col z-40">
        {navContent}
      </aside>

      {/* Mobile sidebar */}
      <aside
        className={`fixed left-0 top-0 bottom-0 w-60 bg-surface border-r border-border flex flex-col z-50 md:hidden transition-transform duration-200 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {navContent}
      </aside>
    </>
  );
}
