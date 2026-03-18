import { useEventStore } from '../../stores/eventStore';

export function FeedFilters() {
  const filters = useEventStore((s) => s.filters);
  const setFilters = useEventStore((s) => s.setFilters);

  return (
    <div className="flex gap-2 p-3 border-b border-gray-200 dark:border-gray-700">
      <select
        value={filters.agentId ?? ''}
        onChange={(e) => setFilters({ agentId: e.target.value || undefined })}
        className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
      >
        <option value="">All Agents</option>
        <option value="product_manager">Product Manager</option>
        <option value="developer">Developer</option>
        <option value="qa_engineer">QA Engineer</option>
        <option value="architect">Architect</option>
        <option value="designer">Designer</option>
      </select>

      <select
        value={filters.eventType ?? ''}
        onChange={(e) => setFilters({ eventType: e.target.value || undefined })}
        className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
      >
        <option value="">All Events</option>
        <option value="agent.message">Messages</option>
        <option value="agent.thinking">Thinking</option>
        <option value="agent.tool_call">Tool Calls</option>
        <option value="task.status_changed">Task Updates</option>
        <option value="approval.requested">Approvals</option>
      </select>
    </div>
  );
}
