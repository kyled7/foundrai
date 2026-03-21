import { useTraceStore } from '../../stores/traceStore';
import { timeAgo, formatTokens } from '../../utils/formatters';
import { getTraceDetail } from '../../api/traces';

export function TraceList() {
  const filteredTraces = useTraceStore((s) => s.filteredTraces());
  const selectedTrace = useTraceStore((s) => s.selectedTrace);
  const setSelectedTrace = useTraceStore((s) => s.setSelectedTrace);

  const handleTraceClick = async (trace_id: number) => {
    try {
      const fullTrace = await getTraceDetail(trace_id);
      setSelectedTrace(fullTrace);
    } catch (error) {
      // TODO: Show error message to user via toast notification
      setSelectedTrace(null);
    }
  };

  if (filteredTraces.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 dark:text-gray-400 text-sm">
        No traces found
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-200 dark:divide-gray-700 overflow-y-auto">
      {filteredTraces.map((trace) => {
        const isSelected = selectedTrace?.trace_id === trace.trace_id;

        return (
          <button
            key={trace.trace_id}
            onClick={() => handleTraceClick(trace.trace_id)}
            className={`w-full text-left p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
              isSelected ? 'bg-blue-50 dark:bg-blue-900/20 border-l-2 border-blue-500' : ''
            }`}
          >
            <div className="flex items-start justify-between gap-2 mb-1">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-gray-900 dark:text-gray-100">
                    {trace.agent_role.replace('_', ' ')}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {trace.model}
                  </span>
                </div>
                {trace.thinking && (
                  <p className="text-xs text-gray-600 dark:text-gray-300 mt-1 line-clamp-2">
                    {trace.thinking}
                  </p>
                )}
              </div>
              <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                {timeAgo(trace.timestamp)}
              </span>
            </div>

            <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
              <span>{formatTokens(trace.tokens_used)} tokens</span>
              <span>${trace.cost_usd.toFixed(4)}</span>
              <span>{trace.duration_ms}ms</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
