"use client";

import { useEffect, useState } from "react";
import { api, DashboardStats } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { AlertTriangle } from "lucide-react";

export default function SettingsPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("token")) { window.location.href = "/login"; return; }
    api.getStats().then(setStats).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="text-text-muted">Loading settings...</div></div>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-text-muted">System configuration and status</p>
      </div>

      <Card className="mb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-amber/20 flex items-center justify-center"><AlertTriangle size={24} className="text-amber" /></div>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h2 className="font-semibold">RazorpayX Mode</h2>
              <Badge variant="amber">TEST MODE</Badge>
            </div>
            <p className="text-sm text-text-muted mt-1">No real money will be moved. Safe to experiment.</p>
          </div>
        </div>
        <div className="mt-4 p-3 bg-elevated rounded border border-border">
          <p className="text-xs text-text-muted">
            Mode is controlled by backend <code className="text-cyan">RAZORPAY_MODE</code> env var. Changing to live mode will process real payments.
          </p>
        </div>
      </Card>

      {stats && (
        <Card>
          <CardHeader><CardTitle>System Status</CardTitle></CardHeader>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-3 bg-elevated rounded"><p className="text-xs text-text-muted">Total Agents</p><p className="text-2xl font-bold">{stats.total_agents}</p></div>
            <div className="p-3 bg-elevated rounded"><p className="text-xs text-text-muted">Active Agents</p><p className="text-2xl font-bold text-green">{stats.active_agents}</p></div>
            <div className="p-3 bg-elevated rounded"><p className="text-xs text-text-muted">Frozen Agents</p><p className="text-2xl font-bold text-red">{stats.frozen_agents}</p></div>
            <div className="p-3 bg-elevated rounded"><p className="text-xs text-text-muted">Total Payees</p><p className="text-2xl font-bold">{stats.total_payees}</p></div>
          </div>
        </Card>
      )}
    </div>
  );
}
