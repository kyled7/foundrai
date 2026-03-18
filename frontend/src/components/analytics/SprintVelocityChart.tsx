import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { SprintSummary } from '@/lib/types';

interface SprintVelocityChartProps {
  data: SprintSummary[];
}

export function SprintVelocityChart({ data }: SprintVelocityChartProps) {
  if (data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 flex items-center justify-center h-72 text-muted text-sm">
        No sprint data yet
      </div>
    );
  }

  const chartData = data.map(s => ({
    sprint: `S${s.sprint_number}`,
    completed: s.completed_tasks,
    failed: s.failed_tasks,
    rate: Math.round(s.completion_rate * 100),
  }));

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium text-foreground mb-4">Sprint Velocity</h3>
      <ResponsiveContainer width="100%" height={250}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="sprint" tick={{ fill: '#94a3b8', fontSize: 12 }} />
          <YAxis yAxisId="left" tick={{ fill: '#94a3b8', fontSize: 12 }} />
          <YAxis yAxisId="right" orientation="right" tick={{ fill: '#94a3b8', fontSize: 12 }} domain={[0, 100]} tickFormatter={v => `${v}%`} />
          <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#f1f5f9' }} />
          <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />
          <Bar yAxisId="left" dataKey="completed" fill="#22c55e" name="Completed" radius={[4, 4, 0, 0]} />
          <Bar yAxisId="left" dataKey="failed" fill="#ef4444" name="Failed" radius={[4, 4, 0, 0]} />
          <Line yAxisId="right" type="monotone" dataKey="rate" stroke="#f59e0b" name="Completion %" strokeWidth={2} dot={{ fill: '#f59e0b' }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
