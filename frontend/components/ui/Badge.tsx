import { HTMLAttributes, forwardRef } from "react";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "green" | "red" | "amber" | "cyan" | "purple";
}

function getStatusVariant(status: string): "green" | "red" | "amber" | "default" {
  switch (status) {
    case "active":
    case "approved":
    case "paid":
    case "policy_allowed":
    case "unfreeze":
    case "credit_unfrozen":
    case "repayment_paid":
      return "green";
    case "frozen":
    case "denied":
    case "rejected":
    case "failed":
    case "late":
    case "defaulted":
    case "policy_denied":
    case "freeze":
    case "credit_frozen":
    case "repayment_late":
    case "repayment_defaulted":
      return "red";
    case "pending":
    case "approval_required":
    case "processing":
    case "credit_reserved":
    case "repayment_created":
      return "amber";
    default:
      return "default";
  }
}

const variantStyles: Record<string, string> = {
  default: "bg-surface-warm text-text-secondary",
  green: "bg-safe-bg text-safe",
  red: "bg-danger-bg text-danger",
  amber: "bg-warning-bg text-warning",
  cyan: "bg-surface-warm text-text-secondary",
  purple: "bg-surface-warm text-text-secondary",
};

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = "default", className = "", children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full font-mono text-[11px] font-medium uppercase tracking-wider ${variantStyles[variant]} ${className}`}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = "Badge";
export { Badge, getStatusVariant };
