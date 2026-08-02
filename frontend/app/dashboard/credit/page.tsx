"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, CreditDashboardData, CreditRiskData, CreditAccountDetail } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableEmpty } from "@/components/ui/Table";
import { Modal } from "@/components/ui/Modal";
import { useToast } from "@/components/Toast";
import { Shield, AlertTriangle, CreditCard } from "lucide-react";

function formatPaise(paise: number) {
  return `₹${(paise / 100).toLocaleString("en-IN")}`;
}

function riskBadgeVariant(level: string): "green" | "amber" | "red" {
  if (level === "LOW") return "green";
  if (level === "MEDIUM") return "amber";
  return "red";
}

function CreditSummary({ data }: { data: CreditDashboardData }) {
  const cards = [
    { label: "Total Credit Issued", value: formatPaise(data.total_credit_limit) },
    { label: "Available", value: formatPaise(data.total_available) },
    { label: "Used", value: formatPaise(data.total_used) },
    { label: "Reserved", value: formatPaise(data.total_reserved) },
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

function RiskOverview({ risk }: { risk: CreditRiskData }) {
  return (
    <Card className="mb-8">
      <div className="flex items-center gap-4 mb-4">
        <div className="w-10 h-10 rounded-full bg-surface-warm flex items-center justify-center">
          <Shield size={20} className="text-text-muted" strokeWidth={1.5} />
        </div>
        <div>
          <h2 className="text-lg font-medium text-text-primary">Risk overview</h2>
          <div className="flex items-center gap-3 mt-1">
            <Badge variant={riskBadgeVariant(risk.overall_risk)}>{risk.overall_risk}</Badge>
            <span className="text-xs text-text-muted">Score: {risk.overall_score}</span>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Violations", value: risk.total_violations },
          { label: "Failures", value: risk.total_failures },
          { label: "Defaults", value: risk.total_defaults },
          { label: "Frozen Agents", value: risk.total_frozen },
        ].map((s) => (
          <div key={s.label} className="bg-surface-warm rounded-[10px] p-3 border border-border-cool">
            <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted">{s.label}</p>
            <p className="text-lg font-medium font-mono text-text-primary mt-1">{s.value}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function AgentRiskTable({ agents }: { agents: CreditRiskData["agents"] }) {
  return (
    <Card padding={false}>
      <CardHeader className="px-4 pt-4">
        <CardTitle>Agent risk levels</CardTitle>
        <Link href="/dashboard/credit/risk">
          <Badge variant="cyan" className="cursor-pointer">View details</Badge>
        </Link>
      </CardHeader>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Agent</TableHead>
            <TableHead>Risk Level</TableHead>
            <TableHead>Score</TableHead>
            <TableHead>Violations</TableHead>
            <TableHead>Failures</TableHead>
            <TableHead>Defaults</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {agents.length === 0 ? (
            <TableEmpty colSpan={7} message="No agents found" />
          ) : (
            agents.map((agent) => (
              <TableRow key={agent.agent_id}>
                <TableCell>
                  <Link href={`/dashboard/credit/${agent.agent_id}`} className="text-text-primary hover:underline">
                    {agent.agent_name}
                  </Link>
                </TableCell>
                <TableCell>
                  <Badge variant={riskBadgeVariant(agent.risk_level)}>{agent.risk_level}</Badge>
                </TableCell>
                <TableCell className="font-mono">{agent.risk_score}</TableCell>
                <TableCell className="font-mono">{agent.violations}</TableCell>
                <TableCell className="font-mono">{agent.failures}</TableCell>
                <TableCell className="font-mono text-danger">{agent.defaults}</TableCell>
                <TableCell>
                  <Badge variant={agent.is_frozen ? "red" : "green"}>
                    {agent.is_frozen ? "FROZEN" : "Active"}
                  </Badge>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
}

export default function CreditDashboardPage() {
  const { toast } = useToast();
  const [credit, setCredit] = useState<CreditDashboardData | null>(null);
  const [risk, setRisk] = useState<CreditRiskData | null>(null);
  const [accounts, setAccounts] = useState<CreditAccountDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [showIssueCredit, setShowIssueCredit] = useState<string | null>(null);
  const [creditLoading, setCreditLoading] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("token")) { window.location.href = "/login"; return; }
    Promise.all([
      api.getCreditDashboard().catch(() => null),
      api.getCreditRisk().catch(() => null),
      api.listCreditAccounts().catch(() => ({ accounts: [] })),
    ]).then(([c, r, acc]) => {
      setCredit(c);
      setRisk(r);
      setAccounts(acc?.accounts ?? []);
    }).finally(() => setLoading(false));
  }, []);

  const handleIssueCredit = async () => {
    if (!showIssueCredit) return;
    setCreditLoading(true);
    try {
      await api.issueCredit(showIssueCredit);
      toast("success", "Credit issued successfully");
      setShowIssueCredit(null);
      const acc = await api.listCreditAccounts();
      setAccounts(acc.accounts);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to issue credit";
      toast("error", msg);
    } finally { setCreditLoading(false); }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="text-sm text-text-muted">Loading credit dashboard...</div></div>;
  }

  if (!credit && !risk) {
    return (
      <div className="text-center py-12">
        <AlertTriangle size={40} className="mx-auto text-warning mb-4" strokeWidth={1.5} />
        <p className="text-text-muted">Credit data unavailable — check that the backend is reachable.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-normal text-text-primary">Credit dashboard</h1>
        <p className="text-sm text-text-muted mt-1">Overview of credit allocation and risk across all agents</p>
      </div>

      {credit && <CreditSummary data={credit} />}
      {risk && <RiskOverview risk={risk} />}
      {risk && <AgentRiskTable agents={risk.agents} />}

      {risk && risk.agents.length > 0 && (
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Agent credit status</CardTitle>
          </CardHeader>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Agent</TableHead>
                <TableHead>Credit Status</TableHead>
                <TableHead>Credit Limit</TableHead>
                <TableHead>Available</TableHead>
                <TableHead>Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {risk.agents.map((a) => {
                const acct = accounts.find((ac) => ac.agent_id === a.agent_id);
                return (
                  <TableRow key={a.agent_id}>
                    <TableCell className="font-medium">{a.agent_name}</TableCell>
                    <TableCell>
                      {acct ? (
                        <Badge variant={acct.status === "active" ? "green" : "red"}>{acct.status}</Badge>
                      ) : (
                        <Badge variant="amber">No credit</Badge>
                      )}
                    </TableCell>
                    <TableCell className="font-mono">{acct ? `₹${(acct.credit_limit / 100).toLocaleString("en-IN")}` : "-"}</TableCell>
                    <TableCell className="font-mono">{acct ? `₹${(acct.available_credit / 100).toLocaleString("en-IN")}` : "-"}</TableCell>
                    <TableCell>
                      {!acct && (
                        <Button size="sm" onClick={() => setShowIssueCredit(a.agent_id)}>
                          <CreditCard size={14} /> Issue Credit
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Card>
      )}

      <Modal open={!!showIssueCredit} onClose={() => setShowIssueCredit(null)} title="Issue Credit">
        <p className="text-sm text-text-secondary mb-4">
          This will run underwriting and issue credit. The credit limit will be determined by the underwriting score.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setShowIssueCredit(null)}>Cancel</Button>
          <Button onClick={handleIssueCredit} disabled={creditLoading}>
            {creditLoading ? "Issuing..." : "Issue Credit"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
