import { Download } from 'lucide-react';
import { useTraceStore } from '../../stores/traceStore';
import { TraceFilters } from './TraceFilters';
import { TraceList } from './TraceList';
import { TraceDetail } from './TraceDetail';

export function DecisionTracePanel() {
  const selectedTrace = useTraceStore((s) => s.selectedTrace);

  function handleExport() {
    if (!selectedTrace) return;

    const dataStr = JSON.stringify(selectedTrace, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `trace-${selectedTrace.trace_id}-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header with Export Button */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <h2 className="text-lg font-semibold text-foreground">Decision Traces</h2>
        <button
          onClick={handleExport}
          disabled={!selectedTrace}
          className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-foreground bg-card border border-border rounded-md hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Export selected trace as JSON"
        >
          <Download size={16} />
          Export JSON
        </button>
      </div>

      {/* Main Content: Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel: Filters and List */}
        <div className="w-1/3 min-w-[300px] flex flex-col border-r border-border">
          <TraceFilters />
          <div className="flex-1 overflow-hidden">
            <TraceList />
          </div>
        </div>

        {/* Right Panel: Detail View */}
        <div className="flex-1 overflow-hidden">
          <TraceDetail trace={selectedTrace} />
        </div>
      </div>
    </div>
  );
}
