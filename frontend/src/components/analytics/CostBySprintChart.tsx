import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

interface Props {
  data: Record<string, { total_cost: number; total_tokens: number }>;
}

export function CostBySprintChart({ data }: Props) {
  const chartData = Object.entries(data).map(([sprint, v]) => ({
    sprint: sprint.slice(0, 8),
    cost: Number(v.total_cost.toFixed(4)),
    tokens: v.total_tokens,
  }));

  if (chartData.length === 0) {
    return <p className="text-gray-400 text-sm">No sprint cost data yet.</p>;
  }

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-5">
      <h3 className="text-sm font-semibold mb-4">Cost by Sprint</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="sprint" fontSize={12} />
          <YAxis fontSize={12} />
          <Tooltip formatter={(v) => `$${Number(v).toFixed(4)}`} />
          <Bar dataKey="cost" fill="#3b82f6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
