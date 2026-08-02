import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "ghost" | "danger" | "success" | "secondary";
  size?: "sm" | "md" | "lg";
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", className = "", children, ...props }, ref) => {
    const base = "inline-flex items-center justify-center gap-2 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer";

    const variants: Record<string, string> = {
      primary: "bg-lime text-ink border-none hover:bg-lime-hover",
      ghost: "bg-transparent text-text-primary border-none hover:underline",
      danger: "bg-danger text-text-inverse border-none hover:opacity-90",
      success: "bg-safe text-text-inverse border-none hover:opacity-90",
      secondary: "bg-surface-warm text-text-primary border border-border-cool hover:bg-surface",
    };

    const sizes: Record<string, string> = {
      sm: "h-8 px-3 text-xs rounded-md",
      md: "h-10 px-5 text-sm rounded-[6px]",
      lg: "h-11 px-6 text-sm rounded-[6px]",
    };

    return (
      <button
        ref={ref}
        className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
export { Button };
