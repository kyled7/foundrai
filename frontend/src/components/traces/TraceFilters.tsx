import { useTraceStore } from '../../stores/traceStore';

export function TraceFilters() {
  const filters = useTraceStore((s) => s.filters);
  const setFilters = useTraceStore((s) => s.setFilters);

  return (
    <div className="flex gap-2 p-3 border-b border-gray-200 dark:border-gray-700">
      <select
        value={filters.agentRole ?? ''}
        onChange={(e) => setFilters({ agentRole: e.target.value || undefined })}
        className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
      >
        <option value="">All Agents</option>
        <option value="product_manager">Product Manager</option>
        <option value="developer">Developer</option>
        <option value="qa_engineer">QA Engineer</option>
        <option value="architect">Architect</option>
        <option value="designer">Designer</option>
        <option value="devops">DevOps</option>
      </select>

      <input
        type="datetime-local"
        value={filters.since ?? ''}
        onChange={(e) => setFilters({ since: e.target.value || undefined })}
        placeholder="Since..."
        className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
      />

      {(filters.agentRole || filters.since) && (
        <button
          onClick={() => setFilters({ agentRole: undefined, since: undefined })}
          className="text-sm px-3 py-1 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
        >
          Clear Filters
        </button>
      )}
    </div>
  );
}
