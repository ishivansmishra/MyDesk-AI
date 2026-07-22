import { ReactNode } from 'react';

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-[24px] border border-white/10 bg-[rgba(17,24,39,0.85)] ${className}`}>{children}</div>;
}
