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
import { ArrowLeft, Plus, Lock, Unlock, Wallet, CreditCard, Clock, Power, Send } from "lucide-react";
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
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [showAddPayee, setShowAddPayee] = useState(false);
  const [showRequestPayout, setShowRequestPayout] = useState(false);
  const [showFreezeConfirm, setShowFreezeConfirm] = useState(false);
  const [payeeForm, setPayeeForm] = useState({ label: "", vpa: "", bank_account_number: "", bank_ifsc: "" });
  const [payoutForm, setPayoutForm] = useState({ payee_id: "", amount_paise: 1000, mode: "upi", purpose: "" });
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
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
      })
      .catch(() => { window.location.href = "/login"; })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!localStorage.getItem("token")) { window.location.href = "/login"; return; }
    load();
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
        toast("info", "Payout requires approval — check dashboard");
      } else {
        toast("success", `Payout created: ${res.status}`);
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
    return <div className="flex items-center justify-center h-64"><div className="text-text-muted">Loading agent details...</div></div>;
  }

  if (!agent) {
    return (
      <div className="text-center py-12">
        <p className="text-text-muted">Agent not found</p>
        <Link href="/agents"><Button variant="ghost" className="mt-4">Back to Agents</Button></Link>
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
      <Link href="/agents" className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-primary mb-4">
        <ArrowLeft size={16} /> Back to Agents
      </Link>

      {/* Agent Header */}
      <Card className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-cyan/20 flex items-center justify-center text-cyan"><CreditCard size={24} /></div>
            <div>
              <h1 className="text-xl font-bold">{agent.name}</h1>
              <div className="flex items-center gap-3 mt-1">
                <Badge variant={getStatusVariant(agent.status)}>{agent.status}</Badge>
                <span className="text-xs text-text-muted">ID: {agent.id.slice(0, 8)}...</span>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setShowRequestPayout(true)} disabled={agent.status === "frozen" || payees.length === 0}>
              <Send size={16} /> Request Payout
            </Button>
            <Button variant={agent.status === "frozen" ? "success" : "danger"} onClick={() => setShowFreezeConfirm(true)}>
              {agent.status === "frozen" ? <><Unlock size={16} /> Unfreeze</> : <><Lock size={16} /> Freeze</>}
            </Button>
          </div>
        </div>
      </Card>

      {/* Freeze Confirm Modal */}
      <Modal open={showFreezeConfirm} onClose={() => setShowFreezeConfirm(false)} title={agent.status === "frozen" ? "Unfreeze Agent?" : "Freeze Agent?"}>
        <p className="text-sm text-text-secondary mb-4">
          {agent.status === "frozen"
            ? `Unfreeze "${agent.name}"? Agent will be able to request payouts again.`
            : `Freeze "${agent.name}"? All payout requests will be blocked immediately.`}
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setShowFreezeConfirm(false)}>Cancel</Button>
          <Button variant={agent.status === "frozen" ? "success" : "danger"} onClick={handleToggleFreeze}>
            {agent.status === "frozen" ? "Unfreeze" : "Freeze"}
          </Button>
        </div>
      </Modal>

      {/* Request Payout Modal */}
      <Modal open={showRequestPayout} onClose={() => setShowRequestPayout(false)} title="Request Payout">
        <form onSubmit={handleRequestPayout} className="space-y-4">
          <Select
            label="Payee"
            value={payoutForm.payee_id}
            onChange={(e) => setPayoutForm({ ...payoutForm, payee_id: e.target.value })}
            options={[{ value: "", label: "Select payee" }, ...payees.filter((p) => p.active).map((p) => ({ value: p.id, label: `${p.label} (${p.vpa || p.bank_account_number})` }))]}
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
          <div className="bg-elevated rounded-lg p-3 text-sm">
            <p className="text-text-muted">Amount: <span className="text-text-primary font-medium">{formatPaise(payoutForm.amount_paise)}</span></p>
            <p className="text-text-muted mt-1">Per-tx cap: {formatPaise(agent.per_tx_cap_paise)} | Approval threshold: {formatPaise(agent.approval_threshold_paise)}</p>
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
              {submitting ? "Processing..." : "Submit Request"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Cap Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-cyan"><Wallet size={20} /></div>
            <div>
              <p className="text-xs text-text-muted">Per Tx Cap</p>
              <p className="text-lg font-bold">{formatPaise(agent.per_tx_cap_paise)}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-green"><Wallet size={20} /></div>
            <div>
              <p className="text-xs text-text-muted">Daily Cap</p>
              <p className="text-lg font-bold">{formatPaise(agent.daily_cap_paise)}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center text-amber"><Clock size={20} /></div>
            <div>
              <p className="text-xs text-text-muted">Approval Threshold</p>
              <p className="text-lg font-bold">{formatPaise(agent.approval_threshold_paise)}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border mb-6">
        {tabs.map((tab) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${activeTab === tab.id ? "text-cyan border-b-2 border-cyan" : "text-text-muted hover:text-text-primary"}`}>
            {tab.label}
            {tab.count !== undefined && <span className="ml-2 text-xs bg-elevated px-1.5 py-0.5 rounded">{tab.count}</span>}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <Card>
          <CardHeader><CardTitle>Agent Overview</CardTitle></CardHeader>
          <div className="grid grid-cols-2 gap-4">
            <div><p className="text-xs text-text-muted mb-1">Status</p><Badge variant={getStatusVariant(agent.status)}>{agent.status}</Badge></div>
            <div><p className="text-xs text-text-muted mb-1">Registered Payees</p><p className="text-lg font-bold">{payees.length}</p></div>
            <div><p className="text-xs text-text-muted mb-1">Total Payouts</p><p className="text-lg font-bold">{payouts.length}</p></div>
            <div><p className="text-xs text-text-muted mb-1">Audit Events</p><p className="text-lg font-bold">{auditEntries.length}</p></div>
          </div>
        </Card>
      )}

      {activeTab === "payees" && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-semibold text-text-secondary">Payee Network</h3>
            <Button size="sm" onClick={() => setShowAddPayee(true)}><Plus size={14} /> Add Payee</Button>
          </div>
          <Modal open={showAddPayee} onClose={() => setShowAddPayee(false)} title="Add Payee">
            <form onSubmit={handleAddPayee} className="space-y-4">
              <Input label="Label" placeholder="e.g. Freelancer" value={payeeForm.label} onChange={(e) => setPayeeForm({ ...payeeForm, label: e.target.value })} required />
              <Input label="VPA (UPI)" placeholder="user@upi" value={payeeForm.vpa} onChange={(e) => setPayeeForm({ ...payeeForm, vpa: e.target.value })} />
              <div className="grid grid-cols-2 gap-3">
                <Input label="Bank Account" value={payeeForm.bank_account_number} onChange={(e) => setPayeeForm({ ...payeeForm, bank_account_number: e.target.value })} />
                <Input label="IFSC" value={payeeForm.bank_ifsc} onChange={(e) => setPayeeForm({ ...payeeForm, bank_ifsc: e.target.value })} />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="ghost" onClick={() => setShowAddPayee(false)}>Cancel</Button>
                <Button type="submit" disabled={submitting}>{submitting ? "Adding..." : "Add Payee"}</Button>
              </div>
            </form>
          </Modal>
          <Table>
            <TableHeader><TableRow><TableHead>Label</TableHead><TableHead>VPA</TableHead><TableHead>Bank Account</TableHead><TableHead>Status</TableHead><TableHead>Action</TableHead></TableRow></TableHeader>
            <TableBody>
              {payees.length === 0 ? (
                <TableEmpty colSpan={5} message="No payees yet. Add your first payee." />
              ) : payees.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">{p.label}</TableCell>
                  <TableCell className="text-text-secondary">{p.vpa || "-"}</TableCell>
                  <TableCell className="text-text-secondary">{p.bank_account_number ? `${p.bank_account_number.slice(0, 4)}****` : "-"}</TableCell>
                  <TableCell><Badge variant={p.active ? "green" : "red"}>{p.active ? "Active" : "Inactive"}</Badge></TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm" onClick={async () => {
                      await api.setPayeeActive(agentId, p.id, !p.active);
                      toast("success", `Payee ${p.active ? "deactivated" : "activated"}`);
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
                <TableCell>{formatPaise(p.amount_paise)}</TableCell>
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
