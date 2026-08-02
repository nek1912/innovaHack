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
    return <div className="flex items-center justify-center h-64"><div className="text-text-muted">Loading risk data...</div></div>;
  }

  if (!risk) {
    return (
      <div className="text-center py-12">
        <p className="text-text-muted">No risk data available</p>
        <Link href="/credit" className="text-sm text-cyan hover:underline mt-2 inline-block">Back to Credit Dashboard</Link>
      </div>
    );
  }

  return (
    <div>
      <Link href="/credit" className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-primary mb-4">
        <ArrowLeft size={16} /> Back to Credit Dashboard
      </Link>

      {/* Overall Risk */}
      <Card className="mb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-cyan/20 flex items-center justify-center text-cyan">
            <Shield size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold">Risk Dashboard</h1>
            <div className="flex items-center gap-3 mt-1">
              <Badge variant={riskBadgeVariant(risk.overall_risk)}>{risk.overall_risk}</Badge>
              <span className="text-xs text-text-muted">Score: {risk.overall_score}</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Risk Factors */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-amber"><AlertTriangle size={20} /></div>
            <div>
              <p className="text-xs text-text-muted">Violations (30d)</p>
              <p className="text-xl font-bold font-mono">{risk.total_violations}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-amber"><AlertTriangle size={20} /></div>
            <div>
              <p className="text-xs text-text-muted">Failures (30d)</p>
              <p className="text-xl font-bold font-mono">{risk.total_failures}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-red"><AlertTriangle size={20} /></div>
            <div>
              <p className="text-xs text-text-muted">Defaults</p>
              <p className="text-xl font-bold font-mono text-red">{risk.total_defaults}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-red"><Lock size={20} /></div>
            <div>
              <p className="text-xs text-text-muted">Frozen Agents</p>
              <p className="text-xl font-bold font-mono text-red">{risk.total_frozen}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Agent Risk Table */}
      <Card padding={false}>
        <CardHeader className="px-4 pt-4">
          <CardTitle>Agent Risk Details</CardTitle>
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
    </div>
  );
}
