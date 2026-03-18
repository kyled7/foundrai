import { useState } from 'react';
import type { AgentMetrics } from '@/lib/types';
import { ArrowUpDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AgentPerformanceTableProps {
  data: AgentMetrics[];
}

type SortKey = keyof AgentMetrics;

export function AgentPerformanceTable({ data }: AgentPerformanceTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('total_cost_usd');
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = [...data].sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey];
    const cmp = typeof av === 'number' && typeof bv === 'number' ? av - bv : String(av).localeCompare(String(bv));
    return sortAsc ? cmp : -cmp;
  });

  const toggle = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  };

  const columns: { key: SortKey; label: string; fmt: (v: AgentMetrics) => string }[] = [
    { key: 'agent_role', label: 'Agent', fmt: v => v.agent_role.replace('_', ' ') },
    { key: 'tasks_completed', label: 'Done', fmt: v => String(v.tasks_completed) },
    { key: 'tasks_failed', label: 'Failed', fmt: v => String(v.tasks_failed) },
    { key: 'avg_duration_seconds', label: 'Avg Time', fmt: v => `${Math.round(v.avg_duration_seconds / 60)}m` },
    { key: 'total_cost_usd', label: 'Cost', fmt: v => `$${v.total_cost_usd.toFixed(2)}` },
    { key: 'cost_per_task_usd', label: '$/Task', fmt: v => `$${v.cost_per_task_usd.toFixed(3)}` },
  ];

  if (data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 flex items-center justify-center h-72 text-muted text-sm">
        No agent data yet
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium text-foreground mb-4">Agent Performance</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              {columns.map(col => (
                <th
                  key={col.key}
                  onClick={() => toggle(col.key)}
                  className={cn('text-left py-2 px-2 text-muted text-xs font-medium cursor-pointer hover:text-foreground select-none',
                    col.key !== 'agent_role' && 'text-right'
                  )}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {sortKey === col.key && <ArrowUpDown size={10} />}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map(row => (
              <tr key={row.agent_role} className="border-b border-border/50 hover:bg-background/50">
                {columns.map(col => (
                  <td key={col.key} className={cn('py-2 px-2 text-foreground', col.key !== 'agent_role' && 'text-right')}>
                    {col.key === 'agent_role' ? <span className="capitalize font-medium">{col.fmt(row)}</span> : col.fmt(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
