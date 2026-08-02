import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

interface RiskGaugeProps {
  riskLevel: string;
  riskScore: number;
  label?: string;
}

function riskBadgeVariant(level: string): "green" | "amber" | "red" {
  if (level === "LOW") return "green";
  if (level === "MEDIUM") return "amber";
  return "red";
}

function scoreColor(score: number): string {
  if (score >= 70) return "text-red";
  if (score >= 40) return "text-amber";
  return "text-green";
}

export function RiskGauge({ riskLevel, riskScore, label }: RiskGaugeProps) {
  const barWidth = Math.min(riskScore, 100);
  const barColor =
    riskScore >= 70 ? "bg-red" : riskScore >= 40 ? "bg-amber" : "bg-green";

  return (
    <Card>
      <CardHeader>
        <CardTitle>{label || "Risk Assessment"}</CardTitle>
        <Badge variant={riskBadgeVariant(riskLevel)}>{riskLevel}</Badge>
      </CardHeader>
      <div className="space-y-3">
        <div className="flex items-end justify-between">
          <span className={`text-4xl font-bold font-mono ${scoreColor(riskScore)}`}>
            {riskScore}
          </span>
          <span className="text-xs text-text-muted">/ 100</span>
        </div>
        <div className="w-full h-2 bg-elevated rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${barColor}`}
            style={{ width: `${barWidth}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-text-muted">
          <span>Low Risk</span>
          <span>High Risk</span>
        </div>
      </div>
    </Card>
  );
}
