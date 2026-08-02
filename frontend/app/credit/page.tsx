"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, CreditDashboardData, CreditRiskData } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableEmpty } from "@/components/ui/Table";
import { Button } from "@/components/ui/Button";
import {
  CreditCard,
  AlertTriangle,
  TrendingDown,
  Shield,
  Activity,
} from "lucide-react";

function formatPaise(paise: number) {
  return `₹${(paise / 100).toLocaleString("en-IN")}`;
}

function getRiskVariant(level: string): "green" | "amber" | "red" | "default" {
  const map: Record<string, "green" | "amber" | "red" | "default"> = {
    LOW: "green",
    MEDIUM: "amber",
    HIGH: "red",
    CRITICAL: "red",
  };
  return map[level] || "default";
}

function SummaryCards({ data }: { data: CreditDashboardData }) {
  const cards = [
    { label: "Total Credit Issued", value: formatPaise(data.total_credit_limit), icon: CreditCard, color: "text-cyan" },
    { label: "Available", value: formatPaise(data.total_available), icon: Activity, color: "text-green" },
    { label: "Used", value: formatPaise(data.total_used), icon: TrendingDown, color: "text-amber" },
    { label: "Reserved", value: formatPaise(data.total_reserved), icon: Shield, color: "text-purple" },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
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

function AccountSummary({ data }: { data: CreditDashboardData }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Account Summary</CardTitle>
      </CardHeader>
      <div className="grid grid-cols-3 gap-4">
        <div>
          <p className="text-xs text-text-muted">Total Accounts</p>
          <p className="text-xl font-bold">{data.total_accounts}</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">Active</p>
          <p className="text-xl font-bold text-green">{data.active_accounts}</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">Frozen</p>
          <p className="text-xl font-bold text-red">{data.frozen_accounts}</p>
        </div>
      </div>
    </Card>
  );
}

function RiskOverview({ data }: { data: CreditRiskData }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk Overview</CardTitle>
      </CardHeader>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <p className="text-xs text-text-muted">Overall Risk</p>
          <Badge variant={getRiskVariant(data.overall_risk)}>{data.overall_risk}</Badge>
        </div>
        <div>
          <p className="text-xs text-text-muted">Violations (30d)</p>
          <p className="text-xl font-bold">{data.total_violations}</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">Failures (30d)</p>
          <p className="text-xl font-bold">{data.total_failures}</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">Defaults</p>
          <p className="text-xl font-bold text-red">{data.total_defaults}</p>
        </div>
      </div>
    </Card>
  );
}

function AgentRiskTable({ agents }: { agents: CreditRiskData["agents"] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Agent Risk Levels</CardTitle>
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
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {agents.length === 0 ? (
            <TableEmpty colSpan={7} message="No agents found" />
          ) : (
            agents.map((agent) => (
              <TableRow key={agent.agent_id}>
                <TableCell className="font-medium">{agent.agent_name}</TableCell>
                <TableCell>
                  <Badge variant={getRiskVariant(agent.risk_level)}>{agent.risk_level}</Badge>
                </TableCell>
                <TableCell className="font-mono">{agent.risk_score}</TableCell>
                <TableCell>{agent.violations}</TableCell>
                <TableCell>{agent.failures}</TableCell>
                <TableCell className={agent.defaults > 0 ? "text-red" : ""}>{agent.defaults}</TableCell>
                <TableCell>
                  <Link href={`/agents/${agent.agent_id}`}>
                    <Button variant="ghost" size="sm">View</Button>
                  </Link>
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
  const [dashboard, setDashboard] = useState<CreditDashboardData | null>(null);
  const [risk, setRisk] = useState<CreditRiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [dataError, setDataError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { window.location.href = "/login"; return; }

    Promise.all([
      api.getCreditDashboard().catch(() => null),
      api.getCreditRisk().catch(() => null),
    ]).then(([d, r]) => {
      setDashboard(d);
      setRisk(r);
      if (!d && !r) setDataError("Credit data unavailable — check that the backend is reachable.");
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-text-muted">Loading credit dashboard...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Credit Dashboard</h1>
        <p className="text-sm text-text-muted">Monitor credit allocation and risk across all agents</p>
      </div>

      {dataError && (
        <div className="mb-4 flex items-center gap-3 bg-amber/10 border border-amber/30 rounded-lg px-4 py-3">
          <AlertTriangle size={18} className="text-amber" aria-hidden="true" />
          <p className="text-sm text-amber">{dataError}</p>
        </div>
      )}

      {dashboard && (
        <>
          <SummaryCards data={dashboard} />
          <div className="mt-6">
            <AccountSummary data={dashboard} />
          </div>
        </>
      )}

      {risk && (
        <div className="mt-6">
          <RiskOverview data={risk} />
        </div>
      )}

      {risk && risk.agents.length > 0 && (
        <div className="mt-6">
          <AgentRiskTable agents={risk.agents} />
        </div>
      )}
    </div>
  );
}