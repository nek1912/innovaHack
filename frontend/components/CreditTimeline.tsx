import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { CreditTransaction } from "@/lib/api";
import { ArrowUpRight, ArrowDownLeft, Minus } from "lucide-react";

interface CreditTimelineProps {
  transactions: CreditTransaction[];
}

function formatPaise(paise: number) {
  return `₹${(paise / 100).toLocaleString("en-IN")}`;
}

const TYPE_CONFIG: Record<string, { variant: "green" | "amber" | "red" | "cyan" | "default"; icon: typeof ArrowUpRight }> = {
  ISSUE: { variant: "green", icon: ArrowDownLeft },
  RESERVE: { variant: "cyan", icon: Minus },
  SPEND: { variant: "amber", icon: ArrowUpRight },
  REPAY: { variant: "green", icon: ArrowDownLeft },
  DEFAULT: { variant: "red", icon: ArrowUpRight },
  FREEZE: { variant: "red", icon: Minus },
  UNFREEZE: { variant: "green", icon: Minus },
  RELEASE: { variant: "cyan", icon: ArrowDownLeft },
};

export function CreditTimeline({ transactions }: CreditTimelineProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Transaction Timeline</CardTitle>
      </CardHeader>
      {transactions.length === 0 ? (
        <p className="text-text-muted text-sm">No transactions yet</p>
      ) : (
        <div className="space-y-3">
          {transactions.map((tx) => {
            const config = TYPE_CONFIG[tx.type] || { variant: "default" as const, icon: Minus };
            const Icon = config.icon;
            return (
              <div key={tx.id} className="flex items-center gap-3 p-3 rounded-lg bg-elevated">
                <div className={`w-8 h-8 rounded flex items-center justify-center text-${config.variant}`}>
                  <Icon size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Badge variant={config.variant}>{tx.type}</Badge>
                    {tx.reason && (
                      <span className="text-xs text-text-muted truncate">{tx.reason}</span>
                    )}
                  </div>
                  <p className="text-xs text-text-muted mt-1">
                    {new Date(tx.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className={`font-mono font-bold ${config.variant === "red" ? "text-red" : config.variant === "green" ? "text-green" : ""}`}>
                    {formatPaise(tx.amount)}
                  </p>
                  <p className="text-xs text-text-muted font-mono">
                    bal: {formatPaise(tx.balance_after)}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
