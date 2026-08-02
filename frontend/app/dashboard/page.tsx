"use client";

import { useEffect, useState } from "react";
import { api, PayoutDetail, AuditEntry, DashboardStats } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, getStatusVariant } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableEmpty } from "@/components/ui/Table";
import { useToast } from "@/components/Toast";
import Link from "next/link";

function formatPaise(paise: number) {
  return `₹${(paise / 100).toLocaleString("en-IN")}`;
}

function SpendBar({ stats }: { stats: DashboardStats }) {
  const limit = stats.today_limit_paise || 1;
  const pct = Math.min((stats.today_spend_paise / limit) * 100, 100);
  const barColor = pct >= 90 ? "bg-danger" : pct >= 70 ? "bg-warning" : "bg-safe";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Today&apos;s spend vs limit</CardTitle>
      </CardHeader>
      <div className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-text-primary">{formatPaise(stats.today_spend_paise)} spent</span>
          <span className="text-text-muted">{formatPaise(stats.today_limit_paise)} limit</span>
        </div>
        <div className="h-2 bg-surface-warm rounded-full overflow-hidden">
          <div className={`h-full ${barColor} rounded-full transition-all`} style={{ width: `${pct}%` }} />
        </div>
        <p className="text-xs text-text-muted">{pct.toFixed(0)}% of daily capacity used</p>
      </div>
    </Card>
  );
}

function SummaryCards({ stats }: { stats: DashboardStats }) {
  const cards = [
    { label: "Total Agents", value: stats.total_agents.toLocaleString("en-IN") },
    { label: "Active", value: stats.active_agents.toLocaleString("en-IN") },
    { label: "Frozen", value: stats.frozen_agents.toLocaleString("en-IN") },
    { label: "Pending Approvals", value: stats.pending_approvals.toLocaleString("en-IN") },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {cards.map((card) => (
        <div key={card.label} className="bg-surface-warm border border-border-cool rounded-[10px] p-5">
          <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted mb-1">{card.label}</p>
          <p className="text-2xl font-normal text-text-primary">{card.value}</p>
        </div>
      ))}
    </div>
  );
}

function HealthCards({ stats }: { stats: DashboardStats }) {
  const success = stats.payment_success_rate;
  const cards = [
    { label: "Provider", value: stats.provider_configured ? (stats.provider_mode || "configured") : "Not configured" },
    { label: "Policy Violations", value: String(stats.policy_violations) },
    { label: "Payment Success", value: success === null ? "—" : `${success.toFixed(1)}%` },
    { label: "Stale / Errors", value: `${stats.stale_payouts} / ${stats.local_error_payouts}` },
    { label: "Last Reconciled", value: stats.last_reconciled_at ? new Date(stats.last_reconciled_at).toLocaleDateString() : "Never" },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
      {cards.map((card) => (
        <div key={card.label} className="bg-surface-warm border border-border-cool rounded-[10px] p-4">
          <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted mb-1">{card.label}</p>
          <p className="text-sm font-medium text-text-primary">{card.value}</p>
        </div>
      ))}
    </div>
  );
}

function ApprovalQueue({ payouts, onApprove, onReject }: { payouts: PayoutDetail[]; onApprove: (id: string) => void; onReject: (id: string) => void }) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Pending approvals</CardTitle>
        <Badge variant="amber">{payouts.length}</Badge>
      </CardHeader>
      {payouts.length === 0 ? (
        <p className="text-sm text-text-muted text-center py-8">No pending approvals</p>
      ) : (
        <div className="space-y-3 max-h-[400px] overflow-y-auto">
          {payouts.map((p) => (
            <div key={p.id} className="bg-surface-warm rounded-[10px] p-4 border border-border-cool">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="text-sm font-medium text-text-primary">{p.agent_name}</p>
                  <p className="text-xs text-text-muted">→ {p.payee_label}</p>
                </div>
                <span className="text-xs text-text-muted">{new Date(p.created_at).toLocaleTimeString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-lg font-medium text-text-primary">{formatPaise(p.amount_paise)}</p>
                  <p className="text-xs text-text-muted">{p.policy_reason || "Above threshold"}</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="danger" size="sm" onClick={() => onReject(p.id)}>Reject</Button>
                  <Button variant="success" size="sm" onClick={() => onApprove(p.id)}>Approve</Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function RecentPayouts({ payouts }: { payouts: PayoutDetail[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent payouts</CardTitle>
        <Link href="/audit">
          <Button variant="ghost" size="sm">View all</Button>
        </Link>
      </CardHeader>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Agent</TableHead>
            <TableHead>Payee</TableHead>
            <TableHead>Amount</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Time</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {payouts.length === 0 ? (
            <TableEmpty colSpan={5} message="No recent payouts" />
          ) : (
            payouts.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="font-medium">{p.agent_name}</TableCell>
                <TableCell className="text-text-secondary">{p.payee_label}</TableCell>
                <TableCell>{formatPaise(p.amount_paise)}</TableCell>
                <TableCell>
                  <Badge variant={getStatusVariant(p.policy_decision)}>
                    {p.policy_decision}
                  </Badge>
                </TableCell>
                <TableCell className="text-text-muted text-xs">
                  {new Date(p.created_at).toLocaleString()}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
}

function AuditPreview({ entries }: { entries: AuditEntry[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit log preview</CardTitle>
        <Link href="/audit">
          <Button variant="ghost" size="sm">View all</Button>
        </Link>
      </CardHeader>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Time</TableHead>
            <TableHead>Event</TableHead>
            <TableHead>Agent</TableHead>
            <TableHead>Details</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {entries.length === 0 ? (
            <TableEmpty colSpan={4} message="No audit entries" />
          ) : (
            entries.map((e) => (
              <TableRow key={e.id}>
                <TableCell className="text-text-muted text-xs">
                  {new Date(e.created_at).toLocaleString()}
                </TableCell>
                <TableCell>
                  <Badge variant={getStatusVariant(e.event_type)}>
                    {e.event_type}
                  </Badge>
                </TableCell>
                <TableCell className="text-text-secondary text-xs">
                  {e.agent_id ? e.agent_id.slice(0, 8) + "..." : "-"}
                </TableCell>
                <TableCell className="text-xs max-w-[200px] truncate">
                  {e.detail ? JSON.stringify(e.detail) : "-"}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [payouts, setPayouts] = useState<PayoutDetail[]>([]);
  const [pendingPayouts, setPendingPayouts] = useState<PayoutDetail[]>([]);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [dataError, setDataError] = useState("");
  const { toast } = useToast();

  const loadData = () => {
    return Promise.all([
      api.getStats().catch(() => null),
      api.listPayouts({ limit: 10 }).catch(() => ({ payouts: [], total: 0 })),
      api.listPayouts({ status: "pending" }).catch(() => ({ payouts: [], total: 0 })),
      api.getAuditLog({ limit: 5 }).catch(() => ({ entries: [], total: 0 })),
    ]).then(([s, p, pending, audit]) => {
      setStats(s);
      if (!s) setDataError("Dashboard stats unavailable — check that the backend is reachable.");
      else setDataError("");
      setPayouts(p.payouts || []);
      setPendingPayouts(pending.payouts || []);
      setAuditEntries(audit.entries || []);
    });
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { window.location.href = "/login"; return; }
    loadData().finally(() => setLoading(false));
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async (id: string) => {
    try {
      await api.approvePayout(id);
      setPendingPayouts((prev) => prev.filter((p) => p.id !== id));
      setStats((s) => s ? { ...s, pending_approvals: s.pending_approvals - 1 } : s);
      toast("success", "Payout approved");
      loadData();
    } catch { toast("error", "Failed to approve payout"); }
  };

  const handleReject = async (id: string) => {
    try {
      await api.rejectPayout(id);
      setPendingPayouts((prev) => prev.filter((p) => p.id !== id));
      setStats((s) => s ? { ...s, pending_approvals: s.pending_approvals - 1 } : s);
      toast("info", "Payout rejected");
      loadData();
    } catch { toast("error", "Failed to reject payout"); }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-text-muted">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-normal text-text-primary">Dashboard</h1>
        <p className="text-sm text-text-muted mt-1">Overview of your agent fleet</p>
      </div>

      {dataError && (
        <div className="mb-6 flex items-center gap-3 bg-warning-bg border border-warning/20 rounded-[10px] px-4 py-3">
          <p className="text-sm text-warning">{dataError}</p>
        </div>
      )}

      {stats && <SummaryCards stats={stats} />}
      {stats && <HealthCards stats={stats} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <RecentPayouts payouts={payouts} />
        </div>
        <div>
          {stats && <SpendBar stats={stats} />}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <AuditPreview entries={auditEntries} />
        </div>
        <div>
          <ApprovalQueue
            payouts={pendingPayouts}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        </div>
      </div>
    </div>
  );
}
