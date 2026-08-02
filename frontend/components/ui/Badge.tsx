type BadgeVariant = "green" | "amber" | "red" | "cyan" | "purple" | "default";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
  pulse?: boolean;
}

const variantStyles: Record<BadgeVariant, string> = {
  green: "bg-green-dim text-green border border-green/30",
  amber: "bg-amber-dim text-amber border border-amber/30",
  red: "bg-red-dim text-red border border-red/30",
  cyan: "bg-cyan-dim text-cyan border border-cyan/30",
  purple: "bg-purple-dim text-purple border border-purple/30",
  default: "bg-elevated text-text-secondary border border-border",
};

export function Badge({ children, variant = "default", className = "", pulse = false }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${variantStyles[variant]} ${pulse ? "animate-pulse-glow" : ""} ${className}`}
    >
      {children}
    </span>
  );
}

export function getStatusVariant(status: string): BadgeVariant {
  const map: Record<string, BadgeVariant> = {
    active: "green",
    frozen: "red",
    approval_required: "amber",
    queued: "cyan",
    processing: "cyan",
    denied: "red",
    rejected: "red",
    processed: "green",
    allow: "green",
    requires_approval: "amber",
    policy_denied: "red",
    policy_allowed: "green",
    approved: "green",
    payout_webhook: "purple",
    payout_requested: "cyan",
    freeze: "red",
    unfreeze: "green",
    failed: "red",
    pending: "amber",
  };
  return map[status] || "default";
}
