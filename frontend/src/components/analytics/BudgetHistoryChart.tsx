import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface BudgetHistoryPoint {
  sprint_id: string;
  sprint_number: number;
  budget_usd: number;
  spent_usd: number;
  remaining_usd: number;
  percentage_used: number;
  is_warning: boolean;
  is_exceeded: boolean;
}

interface BudgetHistoryChartProps {
  data: BudgetHistoryPoint[];
}

export function BudgetHistoryChart({ data }: BudgetHistoryChartProps) {
  if (data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 flex items-center justify-center h-72 text-muted text-sm">
        No budget history yet
      </div>
    );
  }

  const chartData = data.map(s => ({
    sprint: `S${s.sprint_number}`,
    budget: parseFloat(s.budget_usd.toFixed(2)),
    spent: parseFloat(s.spent_usd.toFixed(2)),
  }));

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium text-foreground mb-4">Budget History</h3>
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
            formatter={(value: number, name: string) => [
              `$${value.toFixed(2)}`,
              name === 'budget' ? 'Budget' : 'Spent'
            ]}
            labelFormatter={l => `Sprint ${l.substring(1)}`}
          />
          <Legend
            wrapperStyle={{
              paddingTop: '10px',
            }}
            iconType="line"
            formatter={value => (
              <span style={{ color: '#94a3b8', fontSize: 12 }}>
                {value === 'budget' ? 'Budget' : 'Spent'}
              </span>
            )}
          />
          <Line
            type="monotone"
            dataKey="budget"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ fill: '#10b981', r: 4 }}
            activeDot={{ r: 6 }}
            name="budget"
          />
          <Line
            type="monotone"
            dataKey="spent"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 4 }}
            activeDot={{ r: 6 }}
            name="spent"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
