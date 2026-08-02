import { ReactNode } from "react";

interface TableProps {
  children: ReactNode;
  className?: string;
}

export function Table({ children, className = "" }: TableProps) {
  return (
    <div className={`border border-border rounded-lg overflow-hidden ${className}`}>
      <table className="w-full text-sm">{children}</table>
    </div>
  );
}

export function TableHeader({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <thead className={`bg-elevated border-b border-border ${className}`}>
      {children}
    </thead>
  );
}

export function TableBody({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <tbody className={className}>{children}</tbody>;
}

export function TableRow({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <tr className={`border-b border-border last:border-0 hover:bg-elevated/50 transition-colors ${className}`}>
      {children}
    </tr>
  );
}

export function TableCell({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <td className={`px-4 py-3 ${className}`}>{children}</td>;
}

export function TableHead({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <th className={`text-left px-4 py-2 text-xs font-medium text-text-secondary uppercase tracking-wide ${className}`}>
      {children}
    </th>
  );
}

export function TableEmpty({ colSpan, message = "No data" }: { colSpan: number; message?: string }) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-4 py-12 text-center text-text-muted">
        {message}
      </td>
    </tr>
  );
}
