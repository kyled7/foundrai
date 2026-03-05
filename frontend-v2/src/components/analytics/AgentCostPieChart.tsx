import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface AgentCostPieChartProps {
  data: Record<string, { cost_usd: number; tokens: number }>;
}

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export function AgentCostPieChart({ data }: AgentCostPieChartProps) {
  const entries = Object.entries(data).map(([role, v]) => ({
    name: role.replace('_', ' '),
    value: v.cost_usd,
    tokens: v.tokens,
  }));

  if (entries.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 flex items-center justify-center h-72 text-muted text-sm">
        No agent cost data
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium text-foreground mb-4">Cost by Agent</h3>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie data={entries} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2}>
            {entries.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#f1f5f9' }}
            formatter={(value: number | undefined) => `$${(value ?? 0).toFixed(2)}`}
          />
          <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
