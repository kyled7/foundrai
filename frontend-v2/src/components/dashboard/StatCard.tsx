import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  loading?: boolean;
  className?: string;
}

export function StatCard({ label, value, icon, loading, className }: StatCardProps) {
  return (
    <div className={cn('bg-card border border-border rounded-lg p-4', className)}>
      <div className="flex items-center justify-between mb-2">
        <p className="text-muted text-sm">{label}</p>
        <span className="text-muted">{icon}</span>
      </div>
      {loading ? (
        <div className="h-8 w-16 animate-pulse bg-border rounded" />
      ) : (
        <p className="text-2xl font-bold text-foreground">{value}</p>
      )}
    </div>
  );
}
