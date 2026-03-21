import { cn } from '@/lib/utils';
import { DateRangePicker } from './DateRangePicker';

export type MetricType = 'all' | 'velocity' | 'quality' | 'cost';

interface MetricFiltersProps {
  dateRange: { from: string; to: string } | null;
  onDateRangeChange: (range: { from: string; to: string } | null) => void;
  metricType: MetricType;
  onMetricTypeChange: (type: MetricType) => void;
}

const METRIC_OPTIONS: { value: MetricType; label: string }[] = [
  { value: 'all', label: 'All Metrics' },
  { value: 'velocity', label: 'Velocity' },
  { value: 'quality', label: 'Quality' },
  { value: 'cost', label: 'Cost' },
];

export function MetricFilters({
  dateRange,
  onDateRangeChange,
  metricType,
  onMetricTypeChange,
}: MetricFiltersProps) {
  return (
    <div className="flex flex-col gap-4">
      {/* Date Range Filter */}
      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium text-muted-foreground">
          Date Range
        </label>
        <DateRangePicker value={dateRange} onChange={onDateRangeChange} />
      </div>

      {/* Metric Type Filter */}
      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium text-muted-foreground">
          Metric Type
        </label>
        <div className="flex items-center gap-1">
          {METRIC_OPTIONS.map((option) => {
            const active = metricType === option.value;
            return (
              <button
                key={option.value}
                onClick={() => onMetricTypeChange(option.value)}
                className={cn(
                  'px-3 py-1.5 rounded text-xs font-medium transition-colors',
                  active
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-card border border-border text-muted hover:text-foreground'
                )}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
