import { ReactNode } from 'react';

export function Button({ children, className = '', loading = false, ...props }: { children: ReactNode; className?: string; loading?: boolean } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center rounded-2xl border border-white/10 bg-white/10 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/15 disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
    >
      {loading ? 'Working…' : children}
    </button>
  );
}
