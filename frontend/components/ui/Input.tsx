import { InputHTMLAttributes, SelectHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, className = "", ...props }, ref) => {
    return (
      <div>
        {label && (
          <label className="block text-xs font-medium text-text-secondary mb-1">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`w-full bg-canvas border border-border-warm rounded-[10px] h-10 px-4 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-ink transition-colors ${className}`}
          {...props}
        />
      </div>
    );
  }
);

Input.displayName = "Input";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, options, className = "", ...props }, ref) => {
    return (
      <div>
        {label && (
          <label className="block text-xs font-medium text-text-secondary mb-1">
            {label}
          </label>
        )}
        <select
          ref={ref}
          className={`w-full bg-canvas border border-border-warm rounded-[10px] h-10 px-4 text-sm text-text-primary focus:outline-none focus:border-ink transition-colors ${className}`}
          {...props}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    );
  }
);

Select.displayName = "Select";

export { Input, Select };
