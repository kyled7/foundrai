import { formatCost } from '@/lib/utils';
import { formatTokens, timeAgo } from '../../utils/formatters';
import type { DecisionTrace } from '../../types';

interface TraceDetailProps {
  trace: DecisionTrace | null;
}

export function TraceDetail({ trace }: TraceDetailProps) {
  if (!trace) {
    return (
      <div className="p-4 text-center text-gray-500 dark:text-gray-400">
        Select a trace to view details
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4 overflow-y-auto">
      {/* Header */}
      <div className="border-b border-border pb-3">
        <div className="flex items-start justify-between mb-2">
          <div>
            <h2 className="text-lg font-semibold text-foreground capitalize">
              {trace.agent_role.replace(/_/g, ' ')}
            </h2>
            <p className="text-sm text-muted">{trace.model}</p>
          </div>
          <span className="text-sm text-muted">{timeAgo(trace.timestamp)}</span>
        </div>

        {/* Metrics Summary */}
        <div className="flex items-center gap-4 text-xs text-muted">
          <div className="flex items-center gap-1">
            <span className="font-medium text-foreground">{formatTokens(trace.tokens_used)}</span>
            <span>tokens</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="font-medium text-foreground">{formatCost(trace.cost_usd)}</span>
            <span>cost</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="font-medium text-foreground">{trace.duration_ms}</span>
            <span>ms</span>
          </div>
        </div>
      </div>

      {/* Thinking Section */}
      {trace.thinking && (
        <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
          <h3 className="font-medium text-purple-800 dark:text-purple-300 mb-2 flex items-center gap-2">
            <span>🧠</span>
            <span>Thinking</span>
          </h3>
          <pre className="text-sm text-purple-700 dark:text-purple-400 whitespace-pre-wrap font-mono">
            {trace.thinking}
          </pre>
        </div>
      )}

      {/* Prompt Section */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
        <h3 className="font-medium text-blue-800 dark:text-blue-300 mb-2 flex items-center gap-2">
          <span>📝</span>
          <span>Prompt</span>
        </h3>
        <pre className="text-sm text-blue-700 dark:text-blue-400 whitespace-pre-wrap font-mono overflow-x-auto">
          {trace.prompt}
        </pre>
      </div>

      {/* Response Section */}
      <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
        <h3 className="font-medium text-green-800 dark:text-green-300 mb-2 flex items-center gap-2">
          <span>💬</span>
          <span>Response</span>
        </h3>
        <pre className="text-sm text-green-700 dark:text-green-400 whitespace-pre-wrap font-mono overflow-x-auto">
          {trace.response}
        </pre>
      </div>

      {/* Tool Calls Section */}
      {trace.tool_calls && trace.tool_calls.length > 0 && (
        <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4">
          <h3 className="font-medium text-orange-800 dark:text-orange-300 mb-2 flex items-center gap-2">
            <span>🔧</span>
            <span>Tool Calls</span>
            <span className="text-xs bg-orange-200 dark:bg-orange-800 text-orange-800 dark:text-orange-200 px-2 py-0.5 rounded">
              {trace.tool_calls.length}
            </span>
          </h3>
          <div className="space-y-3">
            {trace.tool_calls.map((toolCall, idx) => (
              <div
                key={idx}
                className="bg-white dark:bg-gray-800 rounded p-3 border border-orange-200 dark:border-orange-800"
              >
                <div className="font-medium text-orange-800 dark:text-orange-300 mb-2 text-sm">
                  {toolCall.name}
                </div>

                {/* Tool Arguments */}
                <div className="mb-2">
                  <div className="text-xs font-medium text-orange-700 dark:text-orange-400 mb-1">
                    Arguments:
                  </div>
                  <pre className="text-xs text-orange-600 dark:text-orange-500 whitespace-pre-wrap font-mono bg-orange-50 dark:bg-orange-950/30 p-2 rounded overflow-x-auto">
                    {JSON.stringify(toolCall.args, null, 2)}
                  </pre>
                </div>

                {/* Tool Result */}
                {toolCall.result !== undefined && (
                  <div>
                    <div className="text-xs font-medium text-orange-700 dark:text-orange-400 mb-1">
                      Result:
                    </div>
                    <pre className="text-xs text-orange-600 dark:text-orange-500 whitespace-pre-wrap font-mono bg-orange-50 dark:bg-orange-950/30 p-2 rounded overflow-x-auto">
                      {typeof toolCall.result === 'string'
                        ? toolCall.result
                        : JSON.stringify(toolCall.result, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metadata Section */}
      <div className="bg-card border border-border rounded-lg p-4">
        <h3 className="font-medium text-foreground mb-3">📊 Metadata</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-muted">Trace ID:</span>
            <div className="font-mono text-foreground">{trace.trace_id}</div>
          </div>
          {trace.event_id && (
            <div>
              <span className="text-muted">Event ID:</span>
              <div className="font-mono text-foreground">{trace.event_id}</div>
            </div>
          )}
          {trace.task_id && (
            <div>
              <span className="text-muted">Task ID:</span>
              <div className="font-mono text-foreground truncate" title={trace.task_id}>
                {trace.task_id}
              </div>
            </div>
          )}
          {trace.sprint_id && (
            <div>
              <span className="text-muted">Sprint ID:</span>
              <div className="font-mono text-foreground truncate" title={trace.sprint_id}>
                {trace.sprint_id}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
