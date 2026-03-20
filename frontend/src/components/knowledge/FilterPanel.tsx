import { cn } from '@/lib/utils';

export interface FilterState {
  category: string | null;
  sprintId: string | null;
  dateRange: { from: string; to: string } | null;
}

interface FilterPanelProps {
  value: FilterState;
  onChange: (filters: FilterState) => void;
  availableSprints?: { sprint_id: string; sprint_number: number }[];
  className?: string;
}

const CATEGORY_OPTIONS = [
  { label: 'All', value: null },
  { label: 'Process', value: 'process' },
  { label: 'Quality', value: 'quality' },
  { label: 'General', value: 'general' },
  { label: 'Architecture', value: 'architecture' },
  { label: 'Technical', value: 'technical' },
];

const DATE_PRESETS = [
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

export function FilterPanel({
  value,
  onChange,
  availableSprints = [],
  className,
}: FilterPanelProps) {
  const updateCategory = (category: string | null) => {
    onChange({ ...value, category });
  };

  const updateSprint = (sprintId: string | null) => {
    onChange({ ...value, sprintId });
  };

  const updateDateRange = (dateRange: { from: string; to: string } | null) => {
    onChange({ ...value, dateRange });
  };

  const isDateAll = value.dateRange === null;

  return (
    <div className={cn('space-y-4 p-4 bg-card border border-border rounded-lg', className)}>
      {/* Category Filter */}
      <div>
        <label className="block text-xs font-medium text-muted mb-2">Category</label>
        <div className="flex flex-wrap gap-1.5">
          {CATEGORY_OPTIONS.map((option) => {
            const active = value.category === option.value;
            return (
              <button
                key={option.label}
                onClick={() => updateCategory(option.value)}
                className={cn(
                  'px-3 py-1.5 rounded text-xs font-medium transition-colors',
                  active
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-background border border-border text-muted hover:text-foreground'
                )}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Sprint Filter */}
      {availableSprints.length > 0 && (
        <div>
          <label className="block text-xs font-medium text-muted mb-2">Sprint</label>
          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => updateSprint(null)}
              className={cn(
                'px-3 py-1.5 rounded text-xs font-medium transition-colors',
                value.sprintId === null
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-background border border-border text-muted hover:text-foreground'
              )}
            >
              All Sprints
            </button>
            {availableSprints.map((sprint) => {
              const active = value.sprintId === sprint.sprint_id;
              return (
                <button
                  key={sprint.sprint_id}
                  onClick={() => updateSprint(sprint.sprint_id)}
                  className={cn(
                    'px-3 py-1.5 rounded text-xs font-medium transition-colors',
                    active
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-background border border-border text-muted hover:text-foreground'
                  )}
                >
                  Sprint {sprint.sprint_number}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Date Range Filter */}
      <div>
        <label className="block text-xs font-medium text-muted mb-2">Date Range</label>
        <div className="flex items-center gap-1.5">
          {DATE_PRESETS.map((preset) => {
            const from = daysAgo(preset.days);
            const active = !isDateAll && value.dateRange?.from === from;
            return (
              <button
                key={preset.days}
                onClick={() => updateDateRange({ from, to: today() })}
                className={cn(
                  'px-3 py-1.5 rounded text-xs font-medium transition-colors',
                  active
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-background border border-border text-muted hover:text-foreground'
                )}
              >
                {preset.label}
              </button>
            );
          })}
          <button
            onClick={() => updateDateRange(null)}
            className={cn(
              'px-3 py-1.5 rounded text-xs font-medium transition-colors',
              isDateAll
                ? 'bg-primary text-primary-foreground'
                : 'bg-background border border-border text-muted hover:text-foreground'
            )}
          >
            All Time
          </button>
        </div>
      </div>
    </div>
  );
}
