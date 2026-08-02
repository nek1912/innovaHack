"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

interface CreditDecision {
  id: string;
  decision: string;
  score: number;
  reason: string;
  approved_limit: number | null;
  model_version: string;
  created_at: string;
}

export default function UnderwritingPage() {
  const params = useParams();
  const agentId = params.agentId as string;
  const [decision, setDecision] = useState<CreditDecision | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/credit/score/${agentId}`)
      .then((r) => r.json())
      .then((d) => {
        setDecision(d);
        setLoading(false);
      });
  }, [agentId]);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="text-sm text-text-muted">Loading...</div></div>;
  if (!decision) return <div className="flex items-center justify-center h-64"><div className="text-sm text-text-muted">No credit decision found</div></div>;

  const factors = decision.reason.split("; ");

  return (
    <div>
      <Link href={`/dashboard/credit/${agentId}`} className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-primary mb-6">
        <ArrowLeft size={16} /> Back to credit account
      </Link>

      <h1 className="text-3xl font-normal text-text-primary mb-8">Underwriting decision</h1>

      {/* Score */}
      <div className="bg-surface-warm border border-border-cool rounded-[10px] p-6 mb-6">
        <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted mb-2">Credit score</p>
        <div className={`text-6xl font-normal ${
          decision.score >= 80 ? "text-safe" :
          decision.score >= 60 ? "text-warning" :
          "text-danger"
        }`}>
          {decision.score}
        </div>
        <p className="text-sm text-text-muted mt-1">/ 100</p>
      </div>

      {/* Decision */}
      <div className="bg-surface-warm border border-border-cool rounded-[10px] p-5 mb-6">
        <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted mb-1">Decision</p>
        <p className={`text-xl font-medium ${
          decision.decision === "approved" ? "text-safe" : "text-danger"
        }`}>
          {decision.decision.toUpperCase()}
        </p>
      </div>

      {/* Approved Limit */}
      {decision.approved_limit && (
        <div className="bg-surface-warm border border-border-cool rounded-[10px] p-5 mb-6">
          <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted mb-1">Approved limit</p>
          <p className="text-2xl font-mono text-text-primary">
            ₹{(decision.approved_limit / 100).toLocaleString()}
          </p>
        </div>
      )}

      {/* Score Factors */}
      <div className="border border-border-warm rounded-[10px] p-5 mb-6">
        <h2 className="text-sm font-medium text-text-primary mb-4">Score factors</h2>
        <div className="space-y-2">
          {factors.map((factor, i) => {
            const isPositive = factor.startsWith("owner_verified") ||
              factor.startsWith("experienced") ||
              factor.startsWith("good_repayment") ||
              factor.startsWith("long_active") ||
              factor.startsWith("some_experience");
            return (
              <div key={i} className="flex items-center text-sm">
                <span className={`mr-2 ${isPositive ? "text-safe" : "text-danger"}`}>
                  {isPositive ? "✓" : "✗"}
                </span>
                <span className="text-text-primary">{factor}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Meta */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-surface-warm border border-border-cool rounded-[10px] p-5">
          <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted mb-1">Model version</p>
          <p className="font-mono text-sm text-text-primary">{decision.model_version}</p>
        </div>
        <div className="bg-surface-warm border border-border-cool rounded-[10px] p-5">
          <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted mb-1">Decision date</p>
          <p className="text-sm text-text-primary">{new Date(decision.created_at).toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
}
