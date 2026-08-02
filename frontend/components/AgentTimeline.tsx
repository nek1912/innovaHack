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
            return (
              <div
                key={event.id}
                className={`flex items-start space-x-3 p-3 rounded-lg ${style.bg}`}
              >
                <div className={`mt-1 w-2 h-2 rounded-full ${style.dot}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm">{event.message}</p>
                  {event.details && (
                    <pre className="mt-2 text-xs text-text-muted overflow-x-auto">
                      {JSON.stringify(event.details, null, 2)}
                    </pre>
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
