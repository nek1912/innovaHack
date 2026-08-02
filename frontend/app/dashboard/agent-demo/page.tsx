"use client";

import { useEffect, useState } from "react";
import { AgentTimeline } from "@/components/AgentTimeline";
import { api } from "@/lib/api";

interface Task {
  id: string;
  name: string;
  description: string;
  vendor: string;
  amount_paise: number;
  expected_result: string;
  scenario: string;
}

interface TimelineEvent {
  id: string;
  type: "thinking" | "action" | "result" | "error";
  message: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

interface Agent {
  id: string;
  name: string;
  status: string;
}

interface Payee {
  id: string;
  label: string;
  vpa: string | null;
  bank_account: string | null;
}

export default function AgentDemoPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [agentId, setAgentId] = useState("");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [creditInfo, setCreditInfo] = useState<{ available: number; limit: number } | null>(null);
  const [payees, setPayees] = useState<Payee[]>([]);

  useEffect(() => {
    // Load demo tasks from backend
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/agent-demo/tasks`)
      .then((r) => r.json())
      .then((d) => setTasks(d.tasks || []))
      .catch(() => setTasks([]));

    // Load agents list
    api.listAgents().then((d) => setAgents(d.agents || [])).catch(() => setAgents([]));
  }, []);

  // Load credit info when agent changes
  useEffect(() => {
    if (agentId) {
      api.getCreditAccount(agentId)
        .then((d) => setCreditInfo({ available: d.available_credit, limit: d.credit_limit }))
        .catch(() => setCreditInfo(null));
    } else {
      setCreditInfo(null);
    }
  }, [agentId]);

  // Load payees when agent changes
  useEffect(() => {
    if (agentId) {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const token = localStorage.getItem("token");
      fetch(`${API_URL}/agent-demo/tools/payees/${agentId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((r) => r.json())
        .then((d) => setPayees(d.payees || []))
        .catch(() => setPayees([]));
    } else {
      setPayees([]);
    }
  }, [agentId]);

  const addEvent = (type: TimelineEvent["type"], message: string, details?: Record<string, unknown>) => {
    setEvents((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        type,
        message,
        timestamp: new Date().toISOString(),
        details,
      },
    ]);
  };

  const runTask = async (task: Task) => {
    if (!agentId) {
      alert("Please select an agent first");
      return;
    }

    setSelectedTask(task);
    setIsRunning(true);
    setEvents([]);

    addEvent("thinking", `Starting task: ${task.name}`);
    addEvent("thinking", `Analyzing requirements: ${task.description}`);
    addEvent("thinking", `Estimated cost: ₹${(task.amount_paise / 100).toLocaleString()}`);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_URL}/agent-demo/execute`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ agent_id: agentId, task_id: task.id }),
      });

      const result = await response.json();

      if (!response.ok) {
        addEvent("error", result.detail || `HTTP ${response.status}`);
        return;
      }

      addEvent("thinking", result.thinking || "Analyzing task...");

      if (result.action) {
        const actionDetails: Record<string, unknown> = {};
        if (result.params?.payee_id) actionDetails.payee_id = result.params.payee_id;
        if (result.params?.amount_paise) actionDetails.amount_paise = result.params.amount_paise;
        if (result.params?.mode) actionDetails.mode = result.params.mode;
        if (result.params?.purpose) actionDetails.purpose = result.params.purpose;
        addEvent("action", `Calling tool: ${result.action}`, actionDetails);
      }

      const resultDetails: Record<string, unknown> = {};
      if (result.status) resultDetails.status = result.status;
      if (result.payout_result) {
        resultDetails.payout_id = result.payout_result.id;
        resultDetails.provider_status = result.payout_result.status;
      }
      addEvent("result", result.message || "Task completed", resultDetails);
    } catch (error) {
      addEvent("error", `Error: ${error}`);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Autonomous Agent Demo</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          {/* Agent Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Select Agent</label>
            <select
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg bg-elevated text-text-primary focus:outline-none focus:ring-2 focus:ring-cyan"
            >
              <option value="">Select an agent</option>
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name} ({agent.status})
                </option>
              ))}
            </select>
          </div>

          {/* Credit Info */}
          {creditInfo && (
            <div className="mb-6 p-4 bg-elevated border border-border rounded-lg">
              <div className="text-sm text-text-muted mb-2">Available Credit</div>
              <div className="text-2xl font-mono text-success">
                ₹{(creditInfo.available / 100).toLocaleString()}
              </div>
              <div className="text-xs text-text-muted mt-1">
                Limit: ₹{(creditInfo.limit / 100).toLocaleString()}
              </div>
            </div>
          )}

          {/* Payees */}
          {agentId && (
            <div className="mb-6 p-4 bg-elevated border border-border rounded-lg">
              <div className="text-sm font-medium mb-2">Approved Payees</div>
              {payees.length === 0 ? (
                <p className="text-sm text-text-muted">No payees found. Ask the owner to add one.</p>
              ) : (
                <ul className="space-y-1">
                  {payees.map((p) => (
                    <li key={p.id} className="text-sm text-text-secondary">
                      {p.label} — {p.vpa || p.bank_account || "No payment details"}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <h2 className="text-lg font-semibold mb-3">Demo Tasks</h2>
          <div className="space-y-3">
            {tasks.map((task) => (
              <div
                key={task.id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedTask?.id === task.id
                    ? "border-cyan bg-cyan/5"
                    : "border-border hover:border-border-light"
                }`}
                onClick={() => !isRunning && runTask(task)}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium">{task.name}</h3>
                    <p className="text-sm text-text-secondary mt-1">{task.description}</p>
                  </div>
                  <span className="text-sm font-mono text-text-muted">
                    ₹{(task.amount_paise / 100).toLocaleString()}
                  </span>
                </div>
                <div className="mt-2 flex items-center space-x-4 text-xs text-text-muted">
                  <span>Vendor: {task.vendor}</span>
                  <span>Expected: {task.expected_result}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <AgentTimeline events={events} isRunning={isRunning} />
        </div>
      </div>


    </div>
  );
}
