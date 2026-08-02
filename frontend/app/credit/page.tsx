"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, CreditDashboardData, CreditRiskData } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableEmpty } from "@/components/ui/Table";
import { Wallet, TrendingUp, TrendingDown, Lock, Shield, AlertTriangle } from "lucide-react";

function formatPaise(paise: number) {
  return `\u20B9${(paise / 100).toLocaleString("en-IN")}`;
}

function riskBadgeVariant(level: string): "green" | "amber" | "red" {
  if (level === "LOW") return "green";
  if (level === "MEDIUM") return "amber";
  return "red";
}

function CreditSummary({ data }: { data: CreditDashboardData }) {
  const cards = [
    { label: "Total Credit Issued", value: formatPaise(data.total_credit_limit), icon: Wallet, color: "text-cyan" },
    { label: "Available", value: formatPaise(data.total_available), icon: TrendingUp, color: "text-green" },
    { label: "Used", value: formatPaise(data.total_used), icon: TrendingDown, color: "text-amber" },
    { label: "Reserved", value: formatPaise(data.total_reserved), icon: Lock, color: "text-purple" },
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

function RiskOverview({ risk }: { risk: CreditRiskData }) {
  return (
    <Card className="mb-6">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-lg bg-cyan/20 flex items-center justify-center text-cyan">
          <Shield size={24} />
        </div>
        <div>
          <h2 className="text-lg font-bold">Risk Overview</h2>
          <div className="flex items-center gap-3 mt-1">
            <Badge variant={riskBadgeVariant(risk.overall_risk)}>{risk.overall_risk}</Badge>
            <span className="text-xs text-text-muted">Score: {risk.overall_score}</span>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
        <div className="bg-elevated rounded-lg p-3">
          <p className="text-xs text-text-muted">Violations</p>
          <p className="text-lg font-bold font-mono">{risk.total_violations}</p>
        </div>
        <div className="bg-elevated rounded-lg p-3">
          <p className="text-xs text-text-muted">Failures</p>
          <p className="text-lg font-bold font-mono">{risk.total_failures}</p>
        </div>
        <div className="bg-elevated rounded-lg p-3">
          <p className="text-xs text-text-muted">Defaults</p>
          <p className="text-lg font-bold font-mono text-red">{risk.total_defaults}</p>
        </div>
        <div className="bg-elevated rounded-lg p-3">
          <p className="text-xs text-text-muted">Frozen Agents</p>
          <p className="text-lg font-bold font-mono text-red">{risk.total_frozen}</p>
        </div>
      </div>
    </Card>
  );
}

function AgentRiskTable({ agents }: { agents: CreditRiskData["agents"] }) {
  return (
    <Card padding={false}>
      <CardHeader className="px-4 pt-4">
        <CardTitle>Agent Risk Levels</CardTitle>
        <Link href="/credit/risk">
          <Badge variant="cyan" className="cursor-pointer">View Details</Badge>
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
                  <Link href={`/credit/${agent.agent_id}`} className="text-cyan hover:underline">
                    {agent.agent_name}
                  </Link>
                </TableCell>
                <TableCell>
                  <Badge variant={riskBadgeVariant(agent.risk_level)}>{agent.risk_level}</Badge>
                </TableCell>
                <TableCell className="font-mono">{agent.risk_score}</TableCell>
                <TableCell className="font-mono">{agent.violations}</TableCell>
                <TableCell className="font-mono">{agent.failures}</TableCell>
                <TableCell className="font-mono text-red">{agent.defaults}</TableCell>
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
  const [credit, setCredit] = useState<CreditDashboardData | null>(null);
  const [risk, setRisk] = useState<CreditRiskData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("token")) { window.location.href = "/login"; return; }
    Promise.all([
      api.getCreditDashboard().catch(() => null),
      api.getCreditRisk().catch(() => null),
    ]).then(([c, r]) => {
      setCredit(c);
      setRisk(r);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="text-text-muted">Loading credit dashboard...</div></div>;
  }

  if (!credit && !risk) {
    return (
      <div className="text-center py-12">
        <AlertTriangle size={48} className="mx-auto text-amber mb-4" />
        <p className="text-text-muted">Credit data unavailable — check that the backend is reachable.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Credit Dashboard</h1>
        <p className="text-sm text-text-muted">Overview of credit allocation and risk across all agents</p>
      </div>

      {credit && <CreditSummary data={credit} />}
      {risk && <RiskOverview risk={risk} />}
      {risk && <AgentRiskTable agents={risk.agents} />}
    </div>
  );
}
