"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, CreditAccountDetail, CreditTransaction } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableEmpty } from "@/components/ui/Table";
import { useToast } from "@/components/Toast";
import { ArrowLeft, Lock, Unlock, AlertTriangle, CreditCard, Activity, TrendingDown, Shield } from "lucide-react";

function formatPaise(paise: number) {
  return `₹${(paise / 100).toLocaleString("en-IN")}`;
}

const TYPE_BADGE: Record<string, "green" | "amber" | "red" | "cyan" | "default"> = {
  ISSUE: "green",
  RESERVE: "cyan",
  SPEND: "amber",
  REPAY: "green",
  DEFAULT: "red",
  FREEZE: "red",
  UNFREEZE: "green",
  RELEASE: "cyan",
};

export default function CreditAccountDetailPage() {
  const params = useParams();
  const agentId = params.agentId as string;
  const { toast } = useToast();

  const [account, setAccount] = useState<CreditAccountDetail | null>(null);
  const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [dataError, setDataError] = useState("");

  useEffect(() => {
    if (!localStorage.getItem("token")) { window.location.href = "/login"; return; }

    Promise.all([
      api.getCreditAccount(agentId).catch(() => null),
      api.getCreditHistory(agentId).catch(() => null),
    ]).then(([a, h]) => {
      setAccount(a);
      setTransactions(h?.transactions || []);
      if (!a) setDataError("Credit account not found or backend unreachable.");
      setLoading(false);
    });
  }, [agentId]);

  const handleToggleFreeze = async () => {
    if (!account) return;
    try {
      if (account.status === "active") {
        await api.freezeCredit(agentId);
        setAccount({ ...account, status: "frozen" });
        toast("success", "Credit frozen");
      } else {
        await api.unfreezeCredit(agentId);
        setAccount({ ...account, status: "active" });
        toast("success", "Credit unfrozen");
      }
    } catch {
      toast("error", "Failed to update credit status");
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="text-text-muted">Loading credit account...</div></div>;
  }

  if (!account) {
    return (
      <div className="text-center py-12">
        <p className="text-text-muted">Credit account not found</p>
        <Link href="/credit"><Button variant="ghost" className="mt-4">Back to Credit Dashboard</Button></Link>
      </div>
    );
  }

  return (
    <div>
      <Link href="/credit" className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-primary mb-4">
        <ArrowLeft size={16} /> Back to Credit Dashboard
      </Link>

      {/* Header */}
      <Card className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-cyan/20 flex items-center justify-center text-cyan"><CreditCard size={24} /></div>
            <div>
              <h1 className="text-xl font-bold">Credit Account</h1>
              <div className="flex items-center gap-3 mt-1">
                <Badge variant={account.status === "active" ? "green" : "red"}>{account.status}</Badge>
                <span className="text-xs text-text-muted">Agent: {agentId.slice(0, 8)}...</span>
              </div>
            </div>
          </div>
          <Button variant={account.status === "active" ? "danger" : "success"} onClick={handleToggleFreeze}>
            {account.status === "active" ? <><Lock size={16} /> Freeze</> : <><Unlock size={16} /> Unfreeze</>}
          </Button>
        </div>
      </Card>

      {dataError && (
        <div className="mb-4 flex items-center gap-3 bg-amber/10 border border-amber/30 rounded-lg px-4 py-3">
          <AlertTriangle size={18} className="text-amber" aria-hidden="true" />
          <p className="text-sm text-amber">{dataError}</p>
        </div>
      )}

      {/* Balance Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-cyan"><CreditCard size={20} /></div>
            <div>
              <p className="text-xs text-text-muted">Credit Limit</p>
              <p className="text-xl font-bold">{formatPaise(account.credit_limit)}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-green"><Activity size={20} /></div>
            <div>
              <p className="text-xs text-text-muted">Available</p>
              <p className="text-xl font-bold text-green">{formatPaise(account.available_credit)}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-purple"><Shield size={20} /></div>
            <div>
              <p className="text-xs text-text-muted">Reserved</p>
              <p className="text-xl font-bold text-purple">{formatPaise(account.reserved_credit)}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-amber"><TrendingDown size={20} /></div>
            <div>
              <p className="text-xs text-text-muted">Used</p>
              <p className="text-xl font-bold text-amber">{formatPaise(account.used_credit)}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Links */}
      <div className="flex gap-4 mb-6">
        <Link href={`/credit/${agentId}/underwriting`} className="text-sm text-cyan hover:underline">View Underwriting</Link>
        <Link href={`/credit/${agentId}/repayments`} className="text-sm text-cyan hover:underline">View Repayments</Link>
      </div>

      {/* Transaction History */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Type</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Balance After</TableHead>
              <TableHead>Reason</TableHead>
              <TableHead>Time</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.length === 0 ? (
              <TableEmpty colSpan={5} message="No transactions yet" />
            ) : (
              transactions.map((tx) => (
                <TableRow key={tx.id}>
                  <TableCell>
                    <Badge variant={TYPE_BADGE[tx.type] || "default"}>{tx.type}</Badge>
                  </TableCell>
                  <TableCell className="font-mono">{formatPaise(tx.amount)}</TableCell>
                  <TableCell className="font-mono text-text-muted">{formatPaise(tx.balance_after)}</TableCell>
                  <TableCell className="text-xs max-w-[200px] truncate">{tx.reason || "-"}</TableCell>
                  <TableCell className="text-text-muted text-xs">{new Date(tx.created_at).toLocaleString()}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
