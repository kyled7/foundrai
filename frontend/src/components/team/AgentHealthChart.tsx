import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { cn } from '@/lib/utils';
import type { AgentHealth } from '@/lib/types';

interface AgentHealthChartProps {
  data: AgentHealth[];
  loading?: boolean;
  className?: string;
}

export function AgentHealthChart({ data, loading, className }: AgentHealthChartProps) {
  if (loading) {
    return (
      <div className={cn('bg-card border border-border rounded-lg p-4', className)}>
        <div className="h-5 w-32 animate-pulse bg-border rounded mb-4" />
        <div className="h-64 animate-pulse bg-border rounded" />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className={cn('bg-card border border-border rounded-lg p-6 flex items-center justify-center h-72 text-muted text-sm', className)}>
        No health data yet
      </div>
    );
  }

  const chartData = data.map((health, index) => ({
    index: index + 1,
    timestamp: new Date(health.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    healthScore: health.health_score,
    completionRate: health.metrics.completion_rate * 100,
    qualityScore: health.metrics.quality_score * 100,
    failureRate: health.metrics.failure_rate * 100,
  }));

  return (
    <div className={cn('bg-card border border-border rounded-lg p-4', className)}>
      <h3 className="text-sm font-medium text-foreground mb-4">Performance Trends</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="timestamp"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
          />
          <YAxis
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            domain={[0, 100]}
            tickFormatter={v => `${v}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: 8,
              color: '#f1f5f9',
            }}
            formatter={(value: number, name: string) => {
              const labels: Record<string, string> = {
                healthScore: 'Health Score',
                completionRate: 'Completion Rate',
                qualityScore: 'Quality Score',
                failureRate: 'Failure Rate',
              };
              return [`${value.toFixed(1)}${name !== 'healthScore' ? '%' : ''}`, labels[name] || name];
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: 12, color: '#94a3b8' }}
            formatter={(value: string) => {
              const labels: Record<string, string> = {
                healthScore: 'Health Score',
                completionRate: 'Completion Rate',
                qualityScore: 'Quality Score',
                failureRate: 'Failure Rate',
              };
              return labels[value] || value;
            }}
          />
          <Line
            type="monotone"
            dataKey="healthScore"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="completionRate"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ fill: '#10b981', r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="qualityScore"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={{ fill: '#8b5cf6', r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="failureRate"
            stroke="#ef4444"
            strokeWidth={2}
            dot={{ fill: '#ef4444', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
