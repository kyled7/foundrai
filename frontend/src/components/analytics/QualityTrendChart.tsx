import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface SprintQualityData {
  sprint_id: string;
  sprint_number: number;
  pass_rate: number;
}

interface QualityTrendChartProps {
  data: SprintQualityData[];
}

export function QualityTrendChart({ data }: QualityTrendChartProps) {
  if (data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 flex items-center justify-center h-72 text-muted text-sm">
        No quality data yet
      </div>
    );
  }

  const chartData = data.map(s => ({
    sprint: `S${s.sprint_number}`,
    passRate: Math.round(s.pass_rate),
  }));

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium text-foreground mb-4">Quality Trend</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="sprint"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
          />
          <YAxis
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            domain={[0, 100]}
            tickFormatter={v => `${v}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: 8,
              color: '#f1f5f9',
            }}
            formatter={(value: number) => [`${value}%`, 'Pass Rate'] as [string, string]}
            labelFormatter={l => `Sprint ${l.substring(1)}`}
          />
          <Line
            type="monotone"
            dataKey="passRate"
            stroke="#22c55e"
            strokeWidth={2}
            dot={{ fill: '#22c55e', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
