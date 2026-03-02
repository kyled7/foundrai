import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

interface Props {
  data: Record<string, { total_cost: number }>;
}

export function CostByAgentChart({ data }: Props) {
  const chartData = Object.entries(data).map(([name, v]) => ({
    name,
    value: Number(v.total_cost.toFixed(4)),
  }));

  if (chartData.length === 0) {
    return <p className="text-gray-400 text-sm">No agent cost data yet.</p>;
  }

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-5">
      <h3 className="text-sm font-semibold mb-4">Cost by Agent</h3>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
            {chartData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(v) => `$${Number(v).toFixed(4)}`} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
