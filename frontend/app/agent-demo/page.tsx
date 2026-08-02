"use client";

import { useEffect, useState } from "react";
import { AgentTimeline } from "@/components/AgentTimeline";

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

export default function AgentDemoPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [agentId, setAgentId] = useState("");

  useEffect(() => {
    fetch("/api/agent-demo/tasks")
      .then((r) => r.json())
      .then((d) => setTasks(d.tasks || []));
  }, []);

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
      alert("Please enter an Agent ID");
      return;
    }

    setSelectedTask(task);
    setIsRunning(true);
    setEvents([]);

    addEvent("thinking", `Starting task: ${task.name}`);
    addEvent("thinking", `Analyzing requirements: ${task.description}`);
    addEvent("thinking", `Estimated cost: ₹${(task.amount_paise / 100).toLocaleString()}`);

    try {
      const response = await fetch("/api/agent-demo/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, task_id: task.id }),
      });

      const result = await response.json();

      addEvent("thinking", result.thinking || "Analyzing task...");

      if (result.action) {
        addEvent("action", `Calling tool: ${result.action}`, result.params);
      }

      addEvent("result", result.message || "Task completed", result);
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
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Agent ID</label>
            <input
              type="text"
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              placeholder="Enter agent UUID"
              className="w-full px-3 py-2 border border-border rounded-lg bg-elevated text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-cyan"
            />
          </div>

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

      <div className="p-6 bg-elevated border border-border rounded-lg">
        <h2 className="text-lg font-semibold mb-4">PS Evaluation Mapping</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="p-3 bg-surface border border-border rounded">
            <div className="font-medium">Trust Design</div>
            <div className="text-text-muted">Underwriting + Credit Issuance</div>
          </div>
          <div className="p-3 bg-surface border border-border rounded">
            <div className="font-medium">Repayment / Credit</div>
            <div className="text-text-muted">Credit Consumption</div>
          </div>
          <div className="p-3 bg-surface border border-border rounded">
            <div className="font-medium">Risk Containment</div>
            <div className="text-text-muted">Credit Exhausted + Frozen</div>
          </div>
          <div className="p-3 bg-surface border border-border rounded">
            <div className="font-medium">Technical Soundness</div>
            <div className="text-text-muted">Duplicate + Webhook + Audit</div>
          </div>
        </div>
      </div>
    </div>
  );
}
