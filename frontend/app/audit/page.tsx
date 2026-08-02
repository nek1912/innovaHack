"use client";

import { useEffect, useState, useTransition } from "react";
import { api, AuditEntry } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge, getStatusVariant } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Input";
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableEmpty } from "@/components/ui/Table";
import { Filter } from "lucide-react";

const EVENT_TYPES = [
  { value: "", label: "All Events" },
  { value: "payout_requested", label: "Payout Requested" },
  { value: "policy_denied", label: "Policy Denied" },
  { value: "policy_allowed", label: "Policy Allowed" },
  { value: "approval_required", label: "Approval Required" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "freeze", label: "Frozen" },
  { value: "unfreeze", label: "Unfrozen" },
  { value: "payout_webhook", label: "Webhook Event" },
  { value: "credit_issued", label: "Credit Issued" },
  { value: "credit_reserved", label: "Credit Reserved" },
  { value: "credit_committed", label: "Credit Committed" },
  { value: "credit_released", label: "Credit Released" },
  { value: "credit_frozen", label: "Credit Frozen" },
  { value: "credit_unfrozen", label: "Credit Unfrozen" },
  { value: "repayment_created", label: "Repayment Created" },
  { value: "repayment_paid", label: "Repayment Paid" },
  { value: "repayment_late", label: "Repayment Late" },
  { value: "repayment_defaulted", label: "Repayment Defaulted" },
];

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ event_type: "", from: "", to: "" });
  const [page, setPage] = useState(0);
  const [isPending, startTransition] = useTransition();
  const limit = 20;

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      window.location.href = "/login";
      return;
    }

    let cancelled = false;

    startTransition(async () => {
      try {
        const d = await api.getAuditLog({ ...filters, limit, offset: page * limit });
        if (!cancelled) {
          setEntries(d.entries);
          setTotal(d.total);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    });

    return () => { cancelled = true; };
  }, [page, filters]);

  const resetFilters = () => {
    setFilters({ event_type: "", from: "", to: "" });
    setPage(0);
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Audit Logs</h1>
        <p className="text-sm text-text-muted">Complete trail of every action and decision</p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2 text-text-muted">
            <Filter size={16} aria-hidden="true" />
            <span className="text-sm font-medium">Filters</span>
          </div>
          <Select
            options={EVENT_TYPES}
            value={filters.event_type}
            onChange={(e) => {
              setFilters({ ...filters, event_type: e.target.value });
              setPage(0);
            }}
            className="w-48"
          />
          <input
            type="date"
            value={filters.from}
            onChange={(e) => setFilters({ ...filters, from: e.target.value })}
            className="bg-elevated border border-border rounded px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-cyan"
            placeholder="From"
          />
          <input
            type="date"
            value={filters.to}
            onChange={(e) => setFilters({ ...filters, to: e.target.value })}
            className="bg-elevated border border-border rounded px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-cyan"
            placeholder="To"
          />
          <Button variant="ghost" size="sm" onClick={resetFilters}>
            Reset
          </Button>
        </div>
      </Card>

      {/* Table */}
      {(loading || isPending) ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-text-muted">Loading audit log...</div>
        </div>
      ) : (
        <Card padding={false}>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Event</TableHead>
                <TableHead>Agent</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.length === 0 ? (
                <TableEmpty colSpan={4} message="No audit entries found" />
              ) : (
                entries.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell className="text-text-muted text-xs whitespace-nowrap">
                      {new Date(e.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusVariant(e.event_type)}>
                        {e.event_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-text-secondary text-xs">
                      {e.agent_id ? e.agent_id.slice(0, 8) + "..." : "-"}
                    </TableCell>
                    <TableCell className="text-xs max-w-[300px] truncate">
                      {e.detail ? (
                        <div className="space-y-1">
                          {typeof e.detail.reason === "string" && (
                            <span className="text-amber">{e.detail.reason}</span>
                          )}
                          {typeof e.detail.payout_id === "string" && (
                            <span className="text-text-muted">Payout: {e.detail.payout_id.slice(0, 8)}...</span>
                          )}
                          {typeof e.detail.amount_paise === "number" && (
                            <span className="text-text-muted">
                              Amount: ₹{(e.detail.amount_paise / 100).toLocaleString("en-IN")}
                            </span>
                          )}
                          {!e.detail.reason && !e.detail.payout_id && !e.detail.amount_paise && (
                            <span>{JSON.stringify(e.detail)}</span>
                          )}
                        </div>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <span className="text-sm text-text-muted">
              {total} total entries
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                disabled={page === 0}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-text-muted">
                Page {page + 1} of {Math.ceil(total / limit) || 1}
              </span>
              <Button
                variant="ghost"
                size="sm"
                disabled={(page + 1) * limit >= total}
                onClick={() => setPage(page + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
