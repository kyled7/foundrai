import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface SprintEfficiencyData {
  sprint_id: string;
  sprint_number: number;
  cost_per_task: number;
}

interface CostEfficiencyChartProps {
  data: SprintEfficiencyData[];
}

export function CostEfficiencyChart({ data }: CostEfficiencyChartProps) {
  if (data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 flex items-center justify-center h-72 text-muted text-sm">
        No efficiency data yet
      </div>
    );
  }

  const chartData = data.map(s => ({
    sprint: `S${s.sprint_number}`,
    costPerTask: parseFloat(s.cost_per_task.toFixed(4)),
  }));

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium text-foreground mb-4">Cost Efficiency</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="sprint"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
          />
          <YAxis
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            tickFormatter={v => `$${v.toFixed(2)}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: 8,
              color: '#f1f5f9',
            }}
            formatter={(value: number) => [`$${value.toFixed(4)}`, 'Cost/Task'] as [string, string]}
            labelFormatter={l => `Sprint ${l.substring(1)}`}
          />
          <Line
            type="monotone"
            dataKey="costPerTask"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={{ fill: '#f59e0b', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
