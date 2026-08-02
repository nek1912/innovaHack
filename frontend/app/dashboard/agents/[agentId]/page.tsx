"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, Agent, Payee, PayoutDetail, AuditEntry } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, getStatusVariant } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableEmpty } from "@/components/ui/Table";
import { useToast } from "@/components/Toast";
import { ArrowLeft, Plus, Lock, Unlock, Wallet, Clock, Power, Send, CreditCard } from "lucide-react";
import Link from "next/link";

function formatPaise(paise: number) {
  return `₹${(paise / 100).toLocaleString("en-IN")}`;
}

type Tab = "overview" | "payees" | "payouts" | "audit";

export default function AgentDetailPage() {
  const params = useParams();
  const agentId = params.agentId as string;
  const { toast } = useToast();

  const [agent, setAgent] = useState<Agent | null>(null);
  const [payees, setPayees] = useState<Payee[]>([]);
  const [payouts, setPayouts] = useState<PayoutDetail[]>([]);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [showAddPayee, setShowAddPayee] = useState(false);
  const [showRequestPayout, setShowRequestPayout] = useState(false);
  const [showFreezeConfirm, setShowFreezeConfirm] = useState(false);
  const [showIssueCredit, setShowIssueCredit] = useState(false);
  const [creditLoading, setCreditLoading] = useState(false);
  const [payeeForm, setPayeeForm] = useState({ label: "", vpa: "", bank_account_number: "", bank_ifsc: "" });
  const [payoutForm, setPayoutForm] = useState({ payee_id: "", amount_paise: 1000, mode: "upi", purpose: "" });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("token")) { window.location.href = "/login"; return; }
    Promise.all([
      api.getAgent(agentId),
      api.listAgentPayees(agentId),
      api.listAgentPayouts(agentId, { limit: 20 }),
      api.getAuditLog({ agent_id: agentId, limit: 20 }),
    ])
      .then(([agentRes, payeesRes, payoutsRes, auditRes]) => {
        setAgent(agentRes);
        setPayees(payeesRes.payees);
        setPayouts(payoutsRes.payouts);
        setAuditEntries(auditRes.entries);
        setLoadError("");
      })
      .catch(() => { setLoadError("Failed to load agent details — check that the backend is reachable."); })
      .finally(() => setLoading(false));
  }, [agentId]);

  const handleToggleFreeze = async () => {
    if (!agent) return;
    try {
      if (agent.status === "frozen") { await api.unfreezeAgent(agentId); toast("success", "Agent unfrozen"); }
      else { await api.freezeAgent(agentId); toast("success", "Agent frozen"); }
      setAgent({ ...agent, status: agent.status === "frozen" ? "active" : "frozen" });
    } catch { toast("error", "Failed to update agent status"); }
    setShowFreezeConfirm(false);
  };

  const handleIssueCredit = async () => {
    setCreditLoading(true);
    try {
      await api.issueCredit(agentId);
      toast("success", "Credit issued successfully");
      setShowIssueCredit(false);
      window.location.reload();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to issue credit";
      toast("error", msg);
    } finally { setCreditLoading(false); }
  };

  const handleAddPayee = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const data: { label: string; vpa?: string; bank_account_number?: string; bank_ifsc?: string } = { label: payeeForm.label };
      if (payeeForm.vpa) data.vpa = payeeForm.vpa;
      if (payeeForm.bank_account_number) data.bank_account_number = payeeForm.bank_account_number;
      if (payeeForm.bank_ifsc) data.bank_ifsc = payeeForm.bank_ifsc;
      await api.createPayee(agentId, data);
      toast("success", "Payee added");
      setShowAddPayee(false);
      setPayeeForm({ label: "", vpa: "", bank_account_number: "", bank_ifsc: "" });
      const res = await api.listAgentPayees(agentId);
      setPayees(res.payees);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to add payee";
      toast("error", msg);
    } finally { setSubmitting(false); }
  };

  const handleRequestPayout = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await api.requestPayout(agentId, {
        payee_id: payoutForm.payee_id,
        amount_paise: payoutForm.amount_paise,
        mode: payoutForm.mode,
        purpose: payoutForm.purpose || undefined,
      });
      if (res.policy_decision === "approval_required") {
        toast("info", "Payout requires approval � check dashboard");
      } else {
        toast("success", "Payout created: " + res.status);
      }
      setShowRequestPayout(false);
      setPayoutForm({ payee_id: "", amount_paise: 1000, mode: "upi", purpose: "" });
      const res2 = await api.listAgentPayouts(agentId, { limit: 20 });
      setPayouts(res2.payouts);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Payout request failed";
      toast("error", msg);
    } finally { setSubmitting(false); }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="text-sm text-text-muted">Loading agent details...</div></div>;
  }

  if (!agent) {
    return (
      <div className="text-center py-12">
        <p className="text-text-muted">{loadError || "Agent not found"}</p>
        <Link href="/dashboard/agents"><Button variant="ghost" className="mt-4">Back to agents</Button></Link>
      </div>
    );
  }

  const tabs: { id: Tab; label: string; count?: number }[] = [
    { id: "overview", label: "Overview" },
    { id: "payees", label: "Payees", count: payees.length },
    { id: "payouts", label: "Payouts", count: payouts.length },
    { id: "audit", label: "Audit" },
  ];

  return (
    <div>
      <Link href="/dashboard/agents" className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-primary mb-6">
        <ArrowLeft size={16} /> Back to agents
      </Link>

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-normal text-text-primary">{agent.name}</h1>
          <div className="flex items-center gap-3 mt-2">
            <Badge variant={getStatusVariant(agent.status)}>{agent.status}</Badge>
            <span className="text-xs text-text-muted font-mono">{agent.id.slice(0, 8)}...</span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowIssueCredit(true)}>
            <CreditCard size={16} /> Issue Credit
          </Button>
          <Button onClick={() => setShowRequestPayout(true)} disabled={agent.status === "frozen" || payees.length === 0}>
            <Send size={16} /> Request payout
          </Button>
          <Button variant={agent.status === "frozen" ? "success" : "danger"} onClick={() => setShowFreezeConfirm(true)}>
            {agent.status === "frozen" ? <><Unlock size={16} /> Unfreeze</> : <><Lock size={16} /> Freeze</>}
          </Button>
        </div>
      </div>

      <Modal open={showFreezeConfirm} onClose={() => setShowFreezeConfirm(false)} title={agent.status === "frozen" ? "Unfreeze agent?" : "Freeze agent?"}>
        <p className="text-sm text-text-secondary mb-4">
          {agent.status === "frozen"
            ? "Unfreeze \"" + agent.name + "\"? Agent will be able to request payouts again."
            : "Freeze \"" + agent.name + "\"? All payout requests will be blocked immediately."}
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setShowFreezeConfirm(false)}>Cancel</Button>
          <Button variant={agent.status === "frozen" ? "success" : "danger"} onClick={handleToggleFreeze}>
            {agent.status === "frozen" ? "Unfreeze" : "Freeze"}
          </Button>
        </div>
      </Modal>

      <Modal open={showIssueCredit} onClose={() => setShowIssueCredit(false)} title="Issue Credit">
        <p className="text-sm text-text-secondary mb-4">
          This will run underwriting and issue credit to "{agent.name}". The credit limit will be determined by the underwriting score.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setShowIssueCredit(false)}>Cancel</Button>
          <Button onClick={handleIssueCredit} disabled={creditLoading}>
            {creditLoading ? "Issuing..." : "Issue Credit"}
          </Button>
        </div>
      </Modal>

      <Modal open={showRequestPayout} onClose={() => setShowRequestPayout(false)} title="Request payout">
        <form onSubmit={handleRequestPayout} className="space-y-4">
          <Select
            label="Payee"
            value={payoutForm.payee_id}
            onChange={(e) => setPayoutForm({ ...payoutForm, payee_id: e.target.value })}
            options={[{ value: "", label: "Select payee" }, ...payees.filter((p) => p.active).map((p) => ({ value: p.id, label: p.label + " (" + (p.vpa || p.bank_account_number) + ")" }))]}
            required
          />
          <Input
            label="Amount (paise)"
            type="number"
            min={1}
            value={payoutForm.amount_paise}
            onChange={(e) => setPayoutForm({ ...payoutForm, amount_paise: +e.target.value })}
            required
          />
          <div className="bg-surface-warm rounded-[10px] p-3 text-sm border border-border-cool">
            <p className="text-text-muted">Amount: <span className="text-text-primary font-medium">{formatPaise(payoutForm.amount_paise)}</span></p>
            <p className="text-text-muted mt-1">Per-tx cap: {formatPaise(agent.per_tx_cap_paise)} � Approval threshold: {formatPaise(agent.approval_threshold_paise)}</p>
          </div>
          <Select
            label="Mode"
            value={payoutForm.mode}
            onChange={(e) => setPayoutForm({ ...payoutForm, mode: e.target.value })}
            options={[{ value: "upi", label: "UPI" }, { value: "imps", label: "IMPS" }, { value: "neft", label: "NEFT" }, { value: "rtgs", label: "RTGS" }]}
          />
          <Input
            label="Purpose (optional)"
            placeholder="e.g. Invoice payment"
            value={payoutForm.purpose}
            onChange={(e) => setPayoutForm({ ...payoutForm, purpose: e.target.value })}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={() => setShowRequestPayout(false)}>Cancel</Button>
            <Button type="submit" disabled={submitting || !payoutForm.payee_id}>
              {submitting ? "Processing..." : "Submit request"}
            </Button>
          </div>
        </form>
      </Modal>

      <Modal open={showAddPayee} onClose={() => setShowAddPayee(false)} title="Add payee">
        <form onSubmit={handleAddPayee} className="space-y-4">
          <Input label="Label" placeholder="e.g. Freelancer" value={payeeForm.label} onChange={(e) => setPayeeForm({ ...payeeForm, label: e.target.value })} required />
          <Input label="VPA (UPI)" placeholder="user@upi" value={payeeForm.vpa} onChange={(e) => setPayeeForm({ ...payeeForm, vpa: e.target.value })} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Bank account" value={payeeForm.bank_account_number} onChange={(e) => setPayeeForm({ ...payeeForm, bank_account_number: e.target.value })} />
            <Input label="IFSC" value={payeeForm.bank_ifsc} onChange={(e) => setPayeeForm({ ...payeeForm, bank_ifsc: e.target.value })} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={() => setShowAddPayee(false)}>Cancel</Button>
            <Button type="submit" disabled={submitting}>{submitting ? "Adding..." : "Add payee"}</Button>
          </div>
        </form>
      </Modal>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {[
          { label: "Per Tx Cap", value: formatPaise(agent.per_tx_cap_paise), icon: Wallet },
          { label: "Daily Cap", value: formatPaise(agent.daily_cap_paise), icon: Wallet },
          { label: "Approval Threshold", value: formatPaise(agent.approval_threshold_paise), icon: Clock },
        ].map((s) => (
          <div key={s.label} className="bg-surface-warm border border-border-cool rounded-[10px] p-4">
            <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted mb-1">{s.label}</p>
            <p className="text-lg font-medium text-text-primary">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="flex gap-0 border-b border-border-cool mb-6">
        {tabs.map((tab) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium transition-colors cursor-pointer ${
              activeTab === tab.id
                ? "text-text-primary border-b-2 border-text-primary"
                : "text-text-muted hover:text-text-primary"
            }`}>
            {tab.label}
            {tab.count !== undefined && <span className="ml-2 text-xs bg-surface-warm px-1.5 py-0.5 rounded-full">{tab.count}</span>}
          </button>
        ))}
      </div>

      {activeTab === "overview" && (
        <Card>
          <CardHeader><CardTitle>Agent overview</CardTitle></CardHeader>
          <div className="grid grid-cols-2 gap-4">
            <div><p className="text-xs text-text-muted mb-1">Status</p><Badge variant={getStatusVariant(agent.status)}>{agent.status}</Badge></div>
            <div><p className="text-xs text-text-muted mb-1">Registered payees</p><p className="text-lg font-medium">{payees.length}</p></div>
            <div><p className="text-xs text-text-muted mb-1">Total payouts</p><p className="text-lg font-medium">{payouts.length}</p></div>
            <div><p className="text-xs text-text-muted mb-1">Audit events</p><p className="text-lg font-medium">{auditEntries.length}</p></div>
          </div>
        </Card>
      )}

      {activeTab === "payees" && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-medium text-text-secondary">Payee network</h3>
            <Button size="sm" onClick={() => setShowAddPayee(true)}><Plus size={14} /> Add payee</Button>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Label</TableHead><TableHead>VPA</TableHead><TableHead>Bank account</TableHead><TableHead>Status</TableHead><TableHead>Action</TableHead></TableRow></TableHeader>
            <TableBody>
              {payees.length === 0 ? (
                <TableEmpty colSpan={5} message="No payees yet. Add your first payee." />
              ) : payees.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">{p.label}</TableCell>
                  <TableCell className="text-text-secondary">{p.vpa || "-"}</TableCell>
                  <TableCell className="text-text-secondary">{p.bank_account_number ? p.bank_account_number.slice(0, 4) + "****" : "-"}</TableCell>
                  <TableCell><Badge variant={p.active ? "green" : "red"}>{p.active ? "Active" : "Inactive"}</Badge></TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm" onClick={async () => {
                      await api.setPayeeActive(agentId, p.id, !p.active);
                      toast("success", "Payee " + (p.active ? "deactivated" : "activated"));
                      const res = await api.listAgentPayees(agentId);
                      setPayees(res.payees);
                    }}><Power size={14} /></Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {activeTab === "payouts" && (
        <Table>
          <TableHeader><TableRow><TableHead>Payee</TableHead><TableHead>Amount</TableHead><TableHead>Mode</TableHead><TableHead>Status</TableHead><TableHead>Provider</TableHead><TableHead>Time</TableHead></TableRow></TableHeader>
          <TableBody>
            {payouts.length === 0 ? <TableEmpty colSpan={6} message="No payouts yet" /> : payouts.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="font-medium">{p.payee_label}</TableCell>
                <TableCell className="font-mono">{formatPaise(p.amount_paise)}</TableCell>
                <TableCell className="uppercase text-xs">{p.mode}</TableCell>
                <TableCell><Badge variant={getStatusVariant(p.policy_decision)}>{p.policy_decision}</Badge></TableCell>
                <TableCell className="text-xs text-text-muted">{p.razorpay_status || "-"}</TableCell>
                <TableCell className="text-text-muted text-xs">{new Date(p.created_at).toLocaleString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {activeTab === "audit" && (
        <Table>
          <TableHeader><TableRow><TableHead>Time</TableHead><TableHead>Event</TableHead><TableHead>Details</TableHead></TableRow></TableHeader>
          <TableBody>
            {auditEntries.length === 0 ? <TableEmpty colSpan={3} message="No audit entries" /> : auditEntries.map((e) => (
              <TableRow key={e.id}>
                <TableCell className="text-text-muted text-xs">{new Date(e.created_at).toLocaleString()}</TableCell>
                <TableCell><Badge variant={getStatusVariant(e.event_type)}>{e.event_type}</Badge></TableCell>
                <TableCell className="text-xs max-w-[300px] truncate">{e.detail ? JSON.stringify(e.detail) : "-"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
