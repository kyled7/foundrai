import { cn } from '@/lib/utils';

interface DateRangePickerProps {
  value: { from: string; to: string } | null;
  onChange: (range: { from: string; to: string } | null) => void;
  presets?: { label: string; days: number }[];
}

const DEFAULT_PRESETS = [
  { label: '7d', days: 7 },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
];

function daysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split('T')[0];
}

function today(): string {
  return new Date().toISOString().split('T')[0];
}

export function DateRangePicker({ value, onChange, presets = DEFAULT_PRESETS }: DateRangePickerProps) {
  const isAll = value === null;

  return (
    <div className="flex items-center gap-1">
      {presets.map(p => {
        const from = daysAgo(p.days);
        const active = !isAll && value?.from === from;
        return (
          <button
            key={p.days}
            onClick={() => onChange({ from, to: today() })}
            className={cn(
              'px-3 py-1.5 rounded text-xs font-medium transition-colors',
              active ? 'bg-primary text-primary-foreground' : 'bg-card border border-border text-muted hover:text-foreground'
            )}
          >
            {p.label}
          </button>
        );
      })}
      <button
        onClick={() => onChange(null)}
        className={cn(
          'px-3 py-1.5 rounded text-xs font-medium transition-colors',
          isAll ? 'bg-primary text-primary-foreground' : 'bg-card border border-border text-muted hover:text-foreground'
        )}
      >
        All
      </button>
    </div>
  );
}
