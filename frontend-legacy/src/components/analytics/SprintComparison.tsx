import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { api } from '../../api/client';

interface SprintMetric {
  sprint_id: string;
  sprint_number: number;
  goal: string;
  task_count: number;
  completed_count: number;
  failed_count: number;
  pass_rate: number;
  total_tokens: number;
  total_cost: number;
  duration_seconds: number;
}

interface Props {
  projectId: string | null;
}

export function SprintComparison({ projectId }: Props) {
  const [sprints, setSprints] = useState<SprintMetric[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    api.get<{ sprints: SprintMetric[] }>(`/projects/${projectId}/sprint-comparison`)
      .then(data => setSprints(data.sprints))
      .finally(() => setLoading(false));
  }, [projectId]);

  if (!projectId) return <p className="text-gray-400 text-sm">Select a project to compare sprints.</p>;
  if (loading) return <p className="text-gray-400 text-sm">Loading...</p>;
  if (sprints.length === 0) return <p className="text-gray-400 text-sm">No sprints to compare.</p>;

  const chartData = sprints.map(s => ({
    name: `Sprint ${s.sprint_number}`,
    pass_rate: s.pass_rate,
    cost: s.total_cost,
  }));

  return (
    <div className="space-y-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="text-sm font-semibold mb-3">📊 Sprint Comparison</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b dark:border-gray-700">
                <th className="pb-2 pr-4">Sprint</th>
                <th className="pb-2 pr-4">Goal</th>
                <th className="pb-2 pr-4">Tasks</th>
                <th className="pb-2 pr-4">✅</th>
                <th className="pb-2 pr-4">❌</th>
                <th className="pb-2 pr-4">Pass Rate</th>
                <th className="pb-2 pr-4">Tokens</th>
                <th className="pb-2 pr-4">Cost</th>
              </tr>
            </thead>
            <tbody>
              {sprints.map(s => (
                <tr key={s.sprint_id} className="border-b dark:border-gray-700">
                  <td className="py-2 pr-4 font-medium">#{s.sprint_number}</td>
                  <td className="py-2 pr-4 truncate max-w-[200px]">{s.goal}</td>
                  <td className="py-2 pr-4">{s.task_count}</td>
                  <td className="py-2 pr-4 text-green-600">{s.completed_count}</td>
                  <td className="py-2 pr-4 text-red-600">{s.failed_count}</td>
                  <td className="py-2 pr-4">{s.pass_rate}%</td>
                  <td className="py-2 pr-4">{s.total_tokens.toLocaleString()}</td>
                  <td className="py-2 pr-4">${s.total_cost.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="text-sm font-semibold mb-3">📈 Trends</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" fontSize={12} />
            <YAxis yAxisId="left" fontSize={12} />
            <YAxis yAxisId="right" orientation="right" fontSize={12} />
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="pass_rate" stroke="#22c55e" name="Pass Rate %" />
            <Line yAxisId="right" type="monotone" dataKey="cost" stroke="#ef4444" name="Cost ($)" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
