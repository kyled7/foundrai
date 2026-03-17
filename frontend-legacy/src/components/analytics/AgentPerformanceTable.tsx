interface AgentRow {
  agent: string;
  tasks: number;
  passRate: string;
  tokens: number;
  cost: number;
}

interface Props {
  agents: AgentRow[];
}

export function AgentPerformanceTable({ agents }: Props) {
  if (agents.length === 0) {
    return <p className="text-gray-400 text-sm">No agent data yet.</p>;
  }

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-5">
      <h3 className="text-sm font-semibold mb-4">Agent Performance</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700 text-left text-gray-500">
            <th className="pb-2">Agent</th>
            <th className="pb-2">Tasks</th>
            <th className="pb-2">Pass Rate</th>
            <th className="pb-2">Tokens</th>
            <th className="pb-2">Cost</th>
          </tr>
        </thead>
        <tbody>
          {agents.map((a) => (
            <tr key={a.agent} className="border-b border-gray-100 dark:border-gray-800">
              <td className="py-2 font-medium">{a.agent}</td>
              <td className="py-2">{a.tasks}</td>
              <td className="py-2">{a.passRate}</td>
              <td className="py-2">{a.tokens.toLocaleString()}</td>
              <td className="py-2">${a.cost.toFixed(4)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
