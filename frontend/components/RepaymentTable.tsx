import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableEmpty } from "@/components/ui/Table";
import { Repayment } from "@/lib/api";

interface RepaymentTableProps {
  repayments: Repayment[];
  onRepay?: (repaymentId: string) => void;
}

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

export function RepaymentTable({ repayments, onRepay }: RepaymentTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Repayment Schedule</CardTitle>
      </CardHeader>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Due Date</TableHead>
            <TableHead>Amount</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Paid</TableHead>
            {onRepay && <TableHead>Actions</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {repayments.length === 0 ? (
            <TableEmpty colSpan={onRepay ? 5 : 4} message="No repayment schedule" />
          ) : (
            repayments.map((r) => (
              <TableRow key={r.id}>
                <TableCell>{new Date(r.due_date).toLocaleDateString()}</TableCell>
                <TableCell className="font-mono">{formatPaise(r.amount)}</TableCell>
                <TableCell>
                  <Badge variant={STATUS_BADGE[r.status] || "default"}>{r.status.toUpperCase()}</Badge>
                </TableCell>
                <TableCell className="font-mono">{formatPaise(r.paid_amount)}</TableCell>
                {onRepay && (
                  <TableCell>
                    {(r.status === "pending" || r.status === "late") && (
                      <Button variant="success" size="sm" onClick={() => onRepay(r.id)}>
                        Pay Now
                      </Button>
                    )}
                  </TableCell>
                )}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
}
