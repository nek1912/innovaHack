"use client";

import { useEffect, useState } from "react";
import { api, PayoutDetail, AuditEntry, DashboardStats } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, getStatusVariant } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableEmpty } from "@/components/ui/Table";
import { useToast } from "@/components/Toast";
import {
  Users,
  UserCheck,
  UserX,
  Wallet,
  TrendingUp,
  Clock,
  XCircle,
  CheckCircle,
  AlertTriangle,
  Shield,
  Activity,
} from "lucide-react";
import Link from "next/link";

function formatPaise(paise: number) {
  return `₹${(paise / 100).toLocaleString("en-IN")}`;
}

function SpendBar({ stats }: { stats: DashboardStats }) {
  const limit = stats.today_limit_paise || 1;
  const pct = Math.min((stats.today_spend_paise / limit) * 100, 100);
  const tone = pct >= 90 ? "bg-red" : pct >= 70 ? "bg-amber" : "bg-green";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Today&apos;s Spend vs Limit</CardTitle>
      </CardHeader>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-text-secondary">{formatPaise(stats.today_spend_paise)} spent</span>
          <span className="text-text-muted">{formatPaise(stats.today_limit_paise)} limit</span>
        </div>
        <div className="h-3 bg-elevated rounded-full overflow-hidden">
          <div className={`h-full ${tone} rounded-full transition-all`} style={{ width: `${pct}%` }} />
        </div>
        <p className="text-xs text-text-muted">{pct.toFixed(0)}% of daily capacity used</p>
      </div>
    </Card>
  );
}

function HealthCards({ stats }: { stats: DashboardStats }) {
  const success = stats.payment_success_rate;
  const successTone = success === null ? "text-text-muted" : success >= 95 ? "text-green" : success >= 80 ? "text-amber" : "text-red";
  const cards = [
    {
      label: "Provider",
      value: stats.provider_configured ? (stats.provider_mode || "configured") : "Not configured",
      icon: Activity,
      color: stats.provider_configured ? "text-green" : "text-red",
    },
    {
      label: "Policy Violations",
      value: stats.policy_violations,
      icon: Shield,
      color: stats.policy_violations > 0 ? "text-amber" : "text-green",
    },
    {
      label: "Payment Success",
      value: success === null ? "—" : `${success.toFixed(1)}%`,
      icon: CheckCircle,
      color: successTone,
    },
    {
      label: "Stale / Local Errors",
      value: `${stats.stale_payouts} / ${stats.local_error_payouts}`,
      icon: AlertTriangle,
      color: stats.stale_payouts + stats.local_error_payouts > 0 ? "text-red" : "text-green",
    },
    {
      label: "Last Reconciled",
      value: stats.last_reconciled_at
        ? new Date(stats.last_reconciled_at).toLocaleString()
        : "Never",
      icon: Activity,
      color: stats.last_reconciled_at ? "text-cyan" : "text-amber",
    },
  ];

  return (
    <div>
      {!stats.provider_configured && (
        <div className="mb-4 flex items-center gap-3 bg-red/10 border border-red/30 rounded-lg px-4 py-3">
          <AlertTriangle size={18} className="text-red" aria-hidden="true" />
          <p className="text-sm text-red">
            Payment provider is not configured — payouts will fail until RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET are set.
          </p>
        </div>
      )}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        {cards.map((card) => (
          <Card key={card.label}>
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg bg-elevated flex items-center justify-center ${card.color}`} aria-hidden="true">
                <card.icon size={20} />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-text-muted">{card.label}</p>
                <p className="text-sm font-bold truncate">{card.value}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

function SummaryCards({ stats }: { stats: DashboardStats }) {
  const cards = [
    { label: "Total Agents", value: stats.total_agents.toLocaleString("en-IN"), icon: Users, color: "text-cyan" },
    { label: "Active Agents", value: stats.active_agents.toLocaleString("en-IN"), icon: UserCheck, color: "text-green" },
    { label: "Frozen Agents", value: stats.frozen_agents.toLocaleString("en-IN"), icon: UserX, color: "text-red" },
    { label: "Total Payees", value: stats.total_payees.toLocaleString("en-IN"), icon: Wallet, color: "text-purple" },
    { label: "Today's Spend", value: formatPaise(stats.today_spend_paise), icon: TrendingUp, color: "text-green" },
    { label: "Today's Limit", value: formatPaise(stats.today_limit_paise), icon: TrendingUp, color: "text-cyan" },
    { label: "Pending Approvals", value: stats.pending_approvals.toLocaleString("en-IN"), icon: Clock, color: "text-amber" },
    { label: "Failed Payouts", value: stats.failed_payouts.toLocaleString("en-IN"), icon: XCircle, color: "text-red" },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card) => (
        <Card key={card.label}>
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg bg-elevated flex items-center justify-center ${card.color}`} aria-hidden="true">
              <card.icon size={20} />
            </div>
            <div>
              <p className="text-xs text-text-muted">{card.label}</p>
              <p className="text-xl font-bold">{card.value}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

function ApprovalQueue({ payouts, onApprove, onReject }: { payouts: PayoutDetail[]; onApprove: (id: string) => void; onReject: (id: string) => void }) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Pending Approvals</CardTitle>
        <Badge variant="amber">{payouts.length}</Badge>
      </CardHeader>
      {payouts.length === 0 ? (
        <p className="text-sm text-text-muted text-center py-8">No pending approvals</p>
      ) : (
        <div className="space-y-3 max-h-[400px] overflow-y-auto">
          {payouts.map((p) => (
            <div key={p.id} className="bg-elevated rounded-lg p-3 border border-border">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="text-sm font-medium">{p.agent_name}</p>
                  <p className="text-xs text-text-muted">→ {p.payee_label}</p>
                </div>
                <span className="text-xs text-text-muted">{new Date(p.created_at).toLocaleTimeString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-lg font-bold">{formatPaise(p.amount_paise)}</p>
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
        <CardTitle>Recent Payouts</CardTitle>
        <Link href="/audit">
          <Button variant="ghost" size="sm">View All</Button>
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
  const eventColors: Record<string, string> = {
    payout_requested: "cyan",
    policy_denied: "red",
    policy_allowed: "green",
    approval_required: "amber",
    approved: "green",
    rejected: "red",
    freeze: "red",
    unfreeze: "green",
    payout_webhook: "purple",
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit Log Preview</CardTitle>
        <Link href="/audit">
          <Button variant="ghost" size="sm">View All</Button>
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
                  <Badge variant={(eventColors[e.event_type] ?? "default") as "cyan" | "red" | "green" | "amber" | "purple" | "default"}>
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
        <div className="text-text-muted">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Dashboard Overview</h1>
        <p className="text-sm text-text-muted">Mission control for your autonomous financial agents</p>
      </div>

      {dataError && (
        <div className="mb-4 flex items-center gap-3 bg-amber/10 border border-amber/30 rounded-lg px-4 py-3">
          <AlertTriangle size={18} className="text-amber" aria-hidden="true" />
          <p className="text-sm text-amber">{dataError}</p>
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
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
