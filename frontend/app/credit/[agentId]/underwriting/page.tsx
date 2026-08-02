"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

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

  if (loading) return <div className="p-6">Loading...</div>;
  if (!decision) return <div className="p-6">No credit decision found</div>;

  const factors = decision.reason.split("; ");

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Underwriting Decision</h1>

      {/* Score */}
      <div className="bg-surface p-6 rounded-lg border border-border">
        <div className="text-secondary mb-2">Credit Score</div>
        <div className={`text-6xl font-bold ${
          decision.score >= 80 ? "text-success" :
          decision.score >= 60 ? "text-warning" :
          "text-danger"
        }`}>
          {decision.score}
        </div>
        <div className="text-secondary text-sm mt-2">/ 100</div>
      </div>

      {/* Decision */}
      <div className="bg-surface p-4 rounded-lg border border-border">
        <div className="text-secondary">Decision</div>
        <div className={`text-xl font-bold ${
          decision.decision === "approved" ? "text-success" : "text-danger"
        }`}>
          {decision.decision.toUpperCase()}
        </div>
      </div>

      {/* Approved Limit */}
      {decision.approved_limit && (
        <div className="bg-surface p-4 rounded-lg border border-border">
          <div className="text-secondary">Approved Limit</div>
          <div className="text-2xl font-mono">
            ₹{(decision.approved_limit / 100).toLocaleString()}
          </div>
        </div>
      )}

      {/* Score Factors */}
      <div className="bg-surface p-4 rounded-lg border border-border">
        <h2 className="text-lg font-semibold mb-4">Score Factors</h2>
        <div className="space-y-2">
          {factors.map((factor, i) => (
            <div key={i} className="flex items-center">
              <span className={`mr-2 ${
                factor.startsWith("owner_verified") ||
                factor.startsWith("experienced") ||
                factor.startsWith("good_repayment") ||
                factor.startsWith("long_active") ||
                factor.startsWith("some_experience")
                  ? "text-success"
                  : "text-danger"
              }`}>
                {factor.startsWith("owner_verified") ||
                 factor.startsWith("experienced") ||
                 factor.startsWith("good_repayment") ||
                 factor.startsWith("long_active") ||
                 factor.startsWith("some_experience")
                  ? "✓"
                  : "✗"}
              </span>
              <span>{factor}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Decision History */}
      <div className="bg-surface p-4 rounded-lg border border-border">
        <div className="text-secondary">Model Version</div>
        <div className="font-mono">{decision.model_version}</div>
      </div>

      <div className="bg-surface p-4 rounded-lg border border-border">
        <div className="text-secondary">Decision Date</div>
        <div>{new Date(decision.created_at).toLocaleString()}</div>
      </div>
    </div>
  );
}
