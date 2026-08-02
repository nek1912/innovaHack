"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, CreditRiskData } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableEmpty } from "@/components/ui/Table";
import { ArrowLeft, Shield, AlertTriangle, Lock } from "lucide-react";

function riskBadgeVariant(level: string): "green" | "amber" | "red" {
  if (level === "LOW") return "green";
  if (level === "MEDIUM") return "amber";
  return "red";
}

export default function RiskDashboard() {
  const [risk, setRisk] = useState<CreditRiskData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("token")) { window.location.href = "/login"; return; }
    api.getCreditRisk()
      .then((d) => setRisk(d))
      .catch(() => setRisk(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="text-sm text-text-muted">Loading risk data...</div></div>;
  }

  if (!risk) {
    return (
      <div className="text-center py-12">
        <p className="text-text-muted">No risk data available</p>
        <Link href="/credit" className="text-sm text-text-muted hover:underline mt-2 inline-block">Back to credit dashboard</Link>
      </div>
    );
  }

  return (
    <div>
      <Link href="/credit" className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-primary mb-6">
        <ArrowLeft size={16} /> Back to credit dashboard
      </Link>

      {/* Overall Risk */}
      <div className="mb-8">
        <h1 className="text-3xl font-normal text-text-primary">Risk dashboard</h1>
        <div className="flex items-center gap-3 mt-2">
          <Badge variant={riskBadgeVariant(risk.overall_risk)}>{risk.overall_risk}</Badge>
          <span className="text-xs text-text-muted">Score: {risk.overall_score}</span>
        </div>
      </div>

      {/* Risk factors */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: "Violations (30d)", value: risk.total_violations },
          { label: "Failures (30d)", value: risk.total_failures },
          { label: "Defaults", value: risk.total_defaults },
          { label: "Frozen Agents", value: risk.total_frozen },
        ].map((s) => (
          <div key={s.label} className="bg-surface-warm border border-border-cool rounded-[10px] p-5">
            <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted mb-1">{s.label}</p>
            <p className="text-2xl font-normal font-mono text-text-primary">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Agent risk table */}
      <Card padding={false}>
        <CardHeader className="px-4 pt-4">
          <CardTitle>Agent risk details</CardTitle>
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
            {risk.agents.length === 0 ? (
              <TableEmpty colSpan={7} message="No agents found" />
            ) : (
              risk.agents.map((agent) => (
                <TableRow key={agent.agent_id}>
                  <TableCell>
                    <Link href={`/credit/${agent.agent_id}`} className="text-text-primary hover:underline">
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
    </div>
  );
}
