"use client";

interface TimelineEvent {
  id: string;
  type: "thinking" | "action" | "result" | "error";
  message: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

interface AgentTimelineProps {
  events: TimelineEvent[];
  isRunning: boolean;
}

const eventStyles = {
  thinking: { bg: "bg-blue/10", dot: "bg-blue" },
  action: { bg: "bg-amber/10", dot: "bg-amber" },
  error: { bg: "bg-red/10", dot: "bg-red" },
  result: { bg: "bg-green/10", dot: "bg-green" },
};

function formatDetailValue(value: unknown): string {
  if (typeof value === "number") return `₹${(value / 100).toLocaleString("en-IN")}`;
  if (typeof value === "string") return value.length > 60 ? value.slice(0, 60) + "..." : value;
  return String(value);
}

function formatTimelineDetails(details: Record<string, unknown>): string[] {
  const parts: string[] = [];
  if (details.payee_id) parts.push(`Payee: ${String(details.payee_id).slice(0, 8)}...`);
  if (typeof details.amount_paise === "number") parts.push(`Amount: ₹${(details.amount_paise / 100).toLocaleString("en-IN")}`);
  if (details.mode) parts.push(`Mode: ${String(details.mode).toUpperCase()}`);
  if (details.purpose) parts.push(`Purpose: ${formatDetailValue(details.purpose)}`);
  if (details.status) parts.push(`Status: ${String(details.status)}`);
  if (details.payout_id) parts.push(`Payout: ${String(details.payout_id).slice(0, 8)}...`);
  if (details.razorpay_payout_id) parts.push(`Provider ID: ${String(details.razorpay_payout_id).slice(0, 12)}...`);
  if (details.provider_status) parts.push(`Provider status: ${String(details.provider_status)}`);
  if (details.provider_error_code) parts.push(`Error: ${details.provider_error_code}`);
  if (details.description) parts.push(String(details.description));
  if (details.error) parts.push(`Error: ${formatDetailValue(details.error)}`);
  if (details.message) parts.push(String(details.message));
  return parts.length > 0 ? parts : ["No details"];
}

export function AgentTimeline({ events, isRunning }: AgentTimelineProps) {
  return (
    <div className="border border-border rounded-lg p-4 bg-surface">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Agent Activity</h3>
        {isRunning && (
          <span className="flex items-center text-sm text-cyan">
            <span className="animate-pulse-glow mr-2">●</span>
            Running...
          </span>
        )}
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {events.length === 0 ? (
          <p className="text-text-muted text-center py-8">
            No activity yet. Start a task to see agent behavior.
          </p>
        ) : (
          events.map((event) => {
            const style = eventStyles[event.type];
            const detailParts = event.details ? formatTimelineDetails(event.details) : [];
            return (
              <div
                key={event.id}
                className={`flex items-start space-x-3 p-3 rounded-lg ${style.bg}`}
              >
                <div className={`mt-1 w-2 h-2 rounded-full ${style.dot}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm">{event.message}</p>
                  {detailParts.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {detailParts.map((part, i) => (
                        <span key={i} className="text-xs bg-surface-warm px-2 py-0.5 rounded text-text-muted">{part}</span>
                      ))}
                    </div>
                  )}
                </div>
                <span className="text-xs text-text-muted whitespace-nowrap">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
