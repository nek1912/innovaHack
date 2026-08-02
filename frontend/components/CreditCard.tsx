import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, getStatusVariant } from "@/components/ui/Badge";
import { CreditCard as CreditCardIcon, Activity, Shield, TrendingDown } from "lucide-react";

interface CreditCardProps {
  limit: number;
  available: number;
  used: number;
  reserved: number;
  status: string;
}

function formatPaise(paise: number) {
  return `₹${(paise / 100).toLocaleString("en-IN")}`;
}

export function CreditCard({ limit, available, used, reserved, status }: CreditCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Credit Summary</CardTitle>
        <Badge variant={getStatusVariant(status)}>{status.toUpperCase()}</Badge>
      </CardHeader>
      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-cyan">
            <CreditCardIcon size={20} />
          </div>
          <div>
            <p className="text-xs text-text-muted">Limit</p>
            <p className="text-xl font-bold font-mono">{formatPaise(limit)}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-green">
            <Activity size={20} />
          </div>
          <div>
            <p className="text-xs text-text-muted">Available</p>
            <p className="text-xl font-bold font-mono text-green">{formatPaise(available)}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-amber">
            <TrendingDown size={20} />
          </div>
          <div>
            <p className="text-xs text-text-muted">Used</p>
            <p className="text-xl font-bold font-mono text-amber">{formatPaise(used)}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-purple">
            <Shield size={20} />
          </div>
          <div>
            <p className="text-xs text-text-muted">Reserved</p>
            <p className="text-xl font-bold font-mono text-purple">{formatPaise(reserved)}</p>
          </div>
        </div>
      </div>
    </Card>
  );
}
