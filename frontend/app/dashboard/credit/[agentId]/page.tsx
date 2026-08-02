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
import { ArrowLeft, Lock, Unlock } from "lucide-react";

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
    return <div className="flex items-center justify-center h-64"><div className="text-sm text-text-muted">Loading credit account...</div></div>;
  }

  if (!account) {
    return (
      <div className="text-center py-12">
        <p className="text-text-muted">Credit account not found</p>
        <Link href="/credit"><Button variant="ghost" className="mt-4">Back to credit dashboard</Button></Link>
      </div>
    );
  }

  return (
    <div>
      <Link href="/credit" className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-primary mb-6">
        <ArrowLeft size={16} /> Back to credit dashboard
      </Link>

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-normal text-text-primary">Credit account</h1>
          <div className="flex items-center gap-3 mt-2">
            <Badge variant={account.status === "active" ? "green" : "red"}>{account.status}</Badge>
            <span className="text-xs text-text-muted font-mono">Agent: {agentId.slice(0, 8)}...</span>
          </div>
        </div>
        <Button variant={account.status === "active" ? "danger" : "success"} onClick={handleToggleFreeze}>
          {account.status === "active" ? <><Lock size={16} /> Freeze</> : <><Unlock size={16} /> Unfreeze</>}
        </Button>
      </div>

      {dataError && (
        <div className="mb-6 flex items-center gap-3 bg-warning-bg border border-warning/20 rounded-[10px] px-4 py-3">
          <p className="text-sm text-warning">{dataError}</p>
        </div>
      )}

      {/* Balance cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: "Credit Limit", value: formatPaise(account.credit_limit) },
          { label: "Available", value: formatPaise(account.available_credit) },
          { label: "Reserved", value: formatPaise(account.reserved_credit) },
          { label: "Used", value: formatPaise(account.used_credit) },
        ].map((s) => (
          <div key={s.label} className="bg-surface-warm border border-border-cool rounded-[10px] p-5">
            <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted mb-1">{s.label}</p>
            <p className="text-2xl font-normal text-text-primary">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Quick links */}
      <div className="flex gap-4 mb-8">
        <Link href={`/credit/${agentId}/underwriting`} className="text-sm text-text-muted hover:text-text-primary hover:underline">View underwriting</Link>
        <Link href={`/credit/${agentId}/repayments`} className="text-sm text-text-muted hover:text-text-primary hover:underline">View repayments</Link>
      </div>

      {/* Transaction history */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction history</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Type</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Balance after</TableHead>
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
