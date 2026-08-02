import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Check, X } from "lucide-react";

interface Factor {
  label: string;
  positive: boolean;
}

interface UnderwritingFactorsProps {
  score: number;
  factors: Factor[];
  modelVersion?: string;
}

export function UnderwritingFactors({ score, factors, modelVersion }: UnderwritingFactorsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Underwriting Factors</CardTitle>
        <span className={`text-2xl font-bold font-mono ${
          score >= 80 ? "text-green" : score >= 60 ? "text-amber" : "text-red"
        }`}>
          {score}
        </span>
      </CardHeader>
      <div className="space-y-2">
        {factors.map((factor, i) => (
          <div key={i} className="flex items-center gap-2 p-2 rounded bg-elevated">
            {factor.positive ? (
              <Check size={16} className="text-green shrink-0" />
            ) : (
              <X size={16} className="text-red shrink-0" />
            )}
            <span className="text-sm">{factor.label}</span>
          </div>
        ))}
      </div>
      {modelVersion && (
        <p className="text-xs text-text-muted mt-3">Model: {modelVersion}</p>
      )}
    </Card>
  );
}
