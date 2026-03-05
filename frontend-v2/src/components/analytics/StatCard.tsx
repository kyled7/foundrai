import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  trend?: { value: number; direction: 'up' | 'down' };
  format?: 'currency' | 'percent' | 'number' | 'duration';
  className?: string;
}

function formatValue(value: string | number, format?: StatCardProps['format']): string {
  if (typeof value === 'string') return value;
  switch (format) {
    case 'currency': return `$${value.toFixed(2)}`;
    case 'percent': return `${(value * 100).toFixed(1)}%`;
    case 'duration': {
      const mins = Math.floor(value / 60);
      const hrs = Math.floor(mins / 60);
      return hrs > 0 ? `${hrs}h ${mins % 60}m` : `${mins}m`;
    }
    default: return String(value);
  }
}

export function StatCard({ label, value, icon, trend, format, className }: StatCardProps) {
  return (
    <div className={cn('bg-card border border-border rounded-lg p-4', className)}>
      <div className="flex items-center justify-between mb-2">
        <p className="text-muted text-sm">{label}</p>
        <span className="text-muted">{icon}</span>
      </div>
      <p className="text-2xl font-bold text-foreground">{formatValue(value, format)}</p>
      {trend && (
        <div className={cn('flex items-center gap-1 mt-1 text-xs',
          trend.direction === 'up' ? 'text-green-400' : 'text-red-400'
        )}>
          {trend.direction === 'up' ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          <span>{trend.value.toFixed(1)}%</span>
        </div>
      )}
    </div>
  );
}
