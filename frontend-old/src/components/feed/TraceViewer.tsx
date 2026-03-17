import { useEffect, useState } from 'react';
import { getTraceDetail, type TraceDetail } from '../../api/traces';

interface Props {
  traceId: number;
}

function CollapsibleSection({ title, children, defaultOpen = false }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded mt-2">
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left px-3 py-2 text-sm font-medium bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t flex justify-between items-center"
      >
        <span>{title}</span>
        <span>{open ? '▼' : '▶'}</span>
      </button>
      {open && (
        <div className="p-3 text-xs overflow-x-auto">
          {children}
        </div>
      )}
    </div>
  );
}

export function TraceViewer({ traceId }: Props) {
  const [trace, setTrace] = useState<TraceDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getTraceDetail(traceId)
      .then(setTrace)
      .catch(() => setTrace(null))
      .finally(() => setLoading(false));
  }, [traceId]);

  if (loading) return <div className="text-xs text-gray-400 py-2">Loading trace...</div>;
  if (!trace) return <div className="text-xs text-red-400 py-2">Failed to load trace</div>;

  return (
    <div className="mt-2 bg-gray-50 dark:bg-gray-900 rounded p-3 space-y-1">
      <div className="flex gap-4 text-xs text-gray-500">
        <span>🤖 {trace.agent_role}</span>
        <span>📊 {trace.tokens_used} tokens</span>
        <span>💰 ${trace.cost_usd.toFixed(4)}</span>
        <span>⏱ {trace.duration_ms}ms</span>
      </div>

      <CollapsibleSection title="📝 Prompt">
        <pre className="whitespace-pre-wrap bg-white dark:bg-gray-950 p-2 rounded">{trace.prompt}</pre>
      </CollapsibleSection>

      {trace.thinking && (
        <CollapsibleSection title="🧠 Thinking">
          <pre className="whitespace-pre-wrap bg-white dark:bg-gray-950 p-2 rounded">{trace.thinking}</pre>
        </CollapsibleSection>
      )}

      {trace.tool_calls.length > 0 && (
        <CollapsibleSection title="🔧 Tool Calls">
          <pre className="whitespace-pre-wrap bg-white dark:bg-gray-950 p-2 rounded">
            {JSON.stringify(trace.tool_calls, null, 2)}
          </pre>
        </CollapsibleSection>
      )}

      <CollapsibleSection title="💬 Response" defaultOpen>
        <pre className="whitespace-pre-wrap bg-white dark:bg-gray-950 p-2 rounded">{trace.response}</pre>
      </CollapsibleSection>
    </div>
  );
}
