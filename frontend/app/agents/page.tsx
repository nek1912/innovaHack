"use client";

import { useEffect, useState } from "react";
import { api, Agent } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge, getStatusVariant } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableEmpty } from "@/components/ui/Table";
import { useToast } from "@/components/Toast";
import { Plus, Shield, Lock, Unlock } from "lucide-react";
import Link from "next/link";

function formatPaise(paise: number) {
  return `₹${(paise / 100).toLocaleString("en-IN")}`;
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showApiKey, setShowApiKey] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", per_tx_cap_paise: 100000, daily_cap_paise: 500000, approval_threshold_paise: 75000 });
  const [creating, setCreating] = useState(false);
  const { toast } = useToast();

  const load = () => {
    api.listAgents()
      .then((d) => setAgents(d.agents))
      .catch(() => { window.location.href = "/login"; })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!localStorage.getItem("token")) { window.location.href = "/login"; return; }
    load();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      const agent = await api.createAgent(form);
      setShowApiKey(agent.api_key || null);
      toast("success", "Agent created");
      setShowCreate(false);
      setForm({ name: "", per_tx_cap_paise: 100000, daily_cap_paise: 500000, approval_threshold_paise: 75000 });
      load();
    } catch { toast("error", "Failed to create agent"); }
    finally { setCreating(false); }
  };

  const toggleFreeze = async (id: string, current: string) => {
    try {
      if (current === "frozen") { await api.unfreezeAgent(id); toast("success", "Agent unfrozen"); }
      else { await api.freezeAgent(id); toast("success", "Agent frozen"); }
      load();
    } catch { toast("error", "Failed to update agent"); }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="text-text-muted">Loading agents...</div></div>;
  }

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold">Agent Management</h1>
          <p className="text-sm text-text-muted">Manage your autonomous financial agents</p>
        </div>
        <Button onClick={() => setShowCreate(true)}><Plus size={16} /> Create New Agent</Button>
      </div>

      {/* API Key Display Modal */}
      <Modal open={!!showApiKey} onClose={() => setShowApiKey(null)} title="Agent Created">
        <div className="space-y-4">
          <div className="bg-elevated rounded-lg p-4">
            <p className="text-sm text-text-muted mb-2">Save this API key — it won&apos;t be shown again:</p>
            <code className="block bg-background rounded px-3 py-2 text-sm font-mono break-all">{showApiKey}</code>
          </div>
          <div className="flex justify-end">
            <Button onClick={() => setShowApiKey(null)}>I&apos;ve saved it</Button>
          </div>
        </div>
      </Modal>

      {/* Create Agent Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create New Agent">
        <form onSubmit={handleCreate} className="space-y-4">
          <Input label="Agent Name" placeholder="e.g. MarketingAI" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <div className="grid grid-cols-3 gap-3">
            <Input label="Per Tx Cap (paise)" type="number" value={form.per_tx_cap_paise} onChange={(e) => setForm({ ...form, per_tx_cap_paise: +e.target.value })} />
            <Input label="Daily Cap (paise)" type="number" value={form.daily_cap_paise} onChange={(e) => setForm({ ...form, daily_cap_paise: +e.target.value })} />
            <Input label="Approval At (paise)" type="number" value={form.approval_threshold_paise} onChange={(e) => setForm({ ...form, approval_threshold_paise: +e.target.value })} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button type="submit" disabled={creating}>{creating ? "Creating..." : "Create Agent"}</Button>
          </div>
        </form>
      </Modal>

      <Card padding={false} className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Agent</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Per Tx Cap</TableHead>
              <TableHead className="text-right">Daily Cap</TableHead>
              <TableHead className="text-right">Approval At</TableHead>
              <TableHead className="center">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {agents.length === 0 ? (
              <TableEmpty colSpan={6} message="No agents yet. Create your first agent to get started." />
            ) : agents.map((a) => (
              <TableRow key={a.id}>
                <TableCell>
                  <Link href={`/agents/${a.id}`} className="font-medium hover:text-cyan transition-colors">{a.name}</Link>
                </TableCell>
                <TableCell><Badge variant={getStatusVariant(a.status)}>{a.status}</Badge></TableCell>
                <TableCell className="text-right">{formatPaise(a.per_tx_cap_paise)}</TableCell>
                <TableCell className="text-right">{formatPaise(a.daily_cap_paise)}</TableCell>
                <TableCell className="text-right">{formatPaise(a.approval_threshold_paise)}</TableCell>
                <TableCell>
                  <div className="flex items-center justify-center gap-2">
                    <Link href={`/agents/${a.id}`}><Button variant="ghost" size="sm"><Shield size={14} /></Button></Link>
                    <Button variant={a.status === "frozen" ? "success" : "danger"} size="sm" onClick={() => toggleFreeze(a.id, a.status)}>
                      {a.status === "frozen" ? <><Unlock size={14} /> Unfreeze</> : <><Lock size={14} /> Freeze</>}
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
