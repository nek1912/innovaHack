"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, Repayment } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableEmpty } from "@/components/ui/Table";
import { useToast } from "@/components/Toast";
import { ArrowLeft } from "lucide-react";

function formatPaise(paise: number) {
  return `₹${(paise / 100).toLocaleString("en-IN")}`;
}

const STATUS_BADGE: Record<string, "green" | "amber" | "red" | "cyan" | "default"> = {
  pending: "amber",
  processing: "cyan",
  paid: "green",
  failed: "red",
  late: "red",
  defaulted: "red",
};

export default function RepaymentsPage() {
  const params = useParams();
  const agentId = params.agentId as string;
  const { toast } = useToast();
  const [repayments, setRepayments] = useState<Repayment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("token")) { window.location.href = "/login"; return; }

    api.getRepayments(agentId)
      .then((d) => { setRepayments(d.repayments || []); setLoading(false); })
      .catch(() => { toast("error", "Failed to load repayments"); setLoading(false); });
  }, [agentId, toast]);

  const handleRepay = async (repaymentId: string) => {
    try {
      await api.repayCredit(repaymentId);
      setRepayments((prev) =>
        prev.map((r) =>
          r.id === repaymentId ? { ...r, status: "paid", paid_amount: r.amount } : r
        )
      );
      toast("success", "Repayment processed (simulated)");
    } catch {
      toast("error", "Failed to process repayment");
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="text-sm text-text-muted">Loading repayments...</div></div>;
  }

  return (
    <div>
      <Link href={`/credit/${agentId}`} className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-primary mb-6">
        <ArrowLeft size={16} /> Back to credit account
      </Link>

      <div className="mb-8">
        <h1 className="text-3xl font-normal text-text-primary">Repayment schedule</h1>
        <p className="text-sm text-text-muted mt-1">Repayment is simulated — owner-initiated via API</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Repayments</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Due date</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Paid</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {repayments.length === 0 ? (
              <TableEmpty colSpan={5} message="No repayment schedule found" />
            ) : (
              repayments.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>{new Date(r.due_date).toLocaleDateString()}</TableCell>
                  <TableCell className="font-mono">{formatPaise(r.amount)}</TableCell>
                  <TableCell>
                    <Badge variant={STATUS_BADGE[r.status] || "default"}>{r.status.toUpperCase()}</Badge>
                  </TableCell>
                  <TableCell className="font-mono">{formatPaise(r.paid_amount)}</TableCell>
                  <TableCell>
                    {(r.status === "pending" || r.status === "late") && (
                      <Button variant="primary" size="sm" onClick={() => handleRepay(r.id)}>
                        Pay now
                      </Button>
                    )}
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
