import { HTMLAttributes, forwardRef } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padding?: boolean;
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ padding = true, className = "", children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`bg-canvas border border-border-warm rounded-[10px] ${padding ? "p-6" : ""} ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";

function CardHeader({ className = "", children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`flex items-center justify-between mb-4 ${className}`} {...props}>
      {children}
    </div>
  );
}

function CardTitle({ className = "", children, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={`text-sm font-medium text-text-primary ${className}`} {...props}>
      {children}
    </h3>
  );
}

export { Card, CardHeader, CardTitle };
