"use client";

import { useEffect, useState } from "react";
import { api, DashboardStats } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export default function SettingsPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("token")) { window.location.href = "/login"; return; }
    api.getStats().then(setStats).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="text-sm text-text-muted">Loading settings...</div></div>;
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-normal text-text-primary">Settings</h1>
        <p className="text-sm text-text-muted mt-1">System configuration and status</p>
      </div>

      <Card className="mb-6">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h2 className="text-sm font-medium text-text-primary">RazorpayX Mode</h2>
              <Badge variant="amber">TEST MODE</Badge>
            </div>
            <p className="text-sm text-text-muted mt-1">No real money will be moved. Safe to experiment.</p>
          </div>
        </div>
        <div className="mt-4 p-3 bg-surface-warm rounded-[10px] border border-border-cool">
          <p className="text-xs text-text-muted">
            Mode is controlled by backend <code className="text-text-primary font-mono">RAZORPAY_MODE</code> env var. Changing to live mode will process real payments.
          </p>
        </div>
      </Card>

      {stats && (
        <Card>
          <CardHeader><CardTitle>System status</CardTitle></CardHeader>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-surface-warm rounded-[10px] p-4">
              <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted">Total Agents</p>
              <p className="text-2xl font-normal text-text-primary mt-1">{stats.total_agents}</p>
            </div>
            <div className="bg-surface-warm rounded-[10px] p-4">
              <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted">Active Agents</p>
              <p className="text-2xl font-normal text-safe mt-1">{stats.active_agents}</p>
            </div>
            <div className="bg-surface-warm rounded-[10px] p-4">
              <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted">Frozen Agents</p>
              <p className="text-2xl font-normal text-danger mt-1">{stats.frozen_agents}</p>
            </div>
            <div className="bg-surface-warm rounded-[10px] p-4">
              <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted">Total Payees</p>
              <p className="text-2xl font-normal text-text-primary mt-1">{stats.total_payees}</p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
