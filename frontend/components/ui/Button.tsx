import { ButtonHTMLAttributes, forwardRef } from "react";

type ButtonVariant = "primary" | "danger" | "ghost" | "success" | "amber";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: "sm" | "md" | "lg";
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: "bg-cyan text-primary-foreground hover:bg-cyan/90",
  danger: "bg-red text-white hover:bg-red/90",
  ghost: "bg-transparent text-text-secondary hover:bg-elevated hover:text-text-primary",
  success: "bg-green text-primary-foreground hover:bg-green/90",
  amber: "bg-amber text-primary-foreground hover:bg-amber/90",
};

const sizeStyles = {
  sm: "px-2 py-1 text-xs",
  md: "px-3 py-1.5 text-sm",
  lg: "px-4 py-2 text-sm",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", className = "", children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={`inline-flex items-center justify-center gap-2 rounded font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
