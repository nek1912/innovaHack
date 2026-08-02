"use client";

import { useEffect, useState, useTransition } from "react";
import { api, AuditEntry } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge, getStatusVariant } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Input";
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableEmpty } from "@/components/ui/Table";

const EVENT_TYPES = [
  { value: "", label: "All events" },
  { value: "payout_requested", label: "Payout requested" },
  { value: "policy_denied", label: "Policy denied" },
  { value: "policy_allowed", label: "Policy allowed" },
  { value: "approval_required", label: "Approval required" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "freeze", label: "Frozen" },
  { value: "unfreeze", label: "Unfrozen" },
  { value: "payout_webhook", label: "Webhook event" },
  { value: "credit_issued", label: "Credit issued" },
  { value: "credit_reserved", label: "Credit reserved" },
  { value: "credit_committed", label: "Credit committed" },
  { value: "credit_released", label: "Credit released" },
  { value: "credit_frozen", label: "Credit frozen" },
  { value: "credit_unfrozen", label: "Credit unfrozen" },
  { value: "repayment_created", label: "Repayment created" },
  { value: "repayment_paid", label: "Repayment paid" },
  { value: "repayment_late", label: "Repayment late" },
  { value: "repayment_defaulted", label: "Repayment defaulted" },
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
      <div className="mb-8">
        <h1 className="text-3xl font-normal text-text-primary">Audit logs</h1>
        <p className="text-sm text-text-muted mt-1">Complete trail of every action and decision</p>
      </div>

      {/* Filters */}
      <div className="bg-surface-warm border border-border-cool rounded-[10px] p-4 mb-6">
        <div className="flex items-center gap-4 flex-wrap">
          <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Filters</span>
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
            className="bg-canvas border border-border-warm rounded-[10px] h-10 px-4 text-sm text-text-primary focus:outline-none focus:border-ink"
          />
          <input
            type="date"
            value={filters.to}
            onChange={(e) => setFilters({ ...filters, to: e.target.value })}
            className="bg-canvas border border-border-warm rounded-[10px] h-10 px-4 text-sm text-text-primary focus:outline-none focus:border-ink"
          />
          <Button variant="ghost" size="sm" onClick={resetFilters}>
            Reset
          </Button>
        </div>
      </div>

      {/* Table */}
      {(loading || isPending) ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-sm text-text-muted">Loading audit log...</div>
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
                            <span className="text-warning">{e.detail.reason}</span>
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
          <div className="flex items-center justify-between px-4 py-3 border-t border-border-cool">
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
