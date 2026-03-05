import { useEffect, useRef, useState } from 'react';
import { FeedEvent } from './FeedEvent';
import { cn } from '@/lib/utils';
import { ArrowDown } from 'lucide-react';
import type { WSEvent } from '@/lib/types';

interface ActivityFeedProps {
  events: WSEvent[];
  filterAgent?: string | null;
  onApprove?: (approvalId: string) => void;
  onReject?: (approvalId: string) => void;
}

export function ActivityFeed({ events, filterAgent, onApprove, onReject }: ActivityFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  const filtered = filterAgent
    ? events.filter(e => (e.data.agent_id as string) === filterAgent || (e.data.agent_role as string) === filterAgent || !e.data.agent_id)
    : events;

  useEffect(() => {
    if (autoScroll) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filtered.length, autoScroll]);

  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
    setAutoScroll(isAtBottom);
  };

  return (
    <div className="relative flex-1 flex flex-col min-h-0">
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-2 space-y-1"
      >
        {filtered.length === 0 && (
          <div className="flex items-center justify-center h-full text-muted text-sm">
            Waiting for activity...
          </div>
        )}
        {filtered.map((event, i) => (
          <FeedEvent key={i} event={event} onApprove={onApprove} onReject={onReject} />
        ))}
        <div ref={bottomRef} />
      </div>

      {!autoScroll && (
        <button
          onClick={() => {
            bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
            setAutoScroll(true);
          }}
          className={cn(
            'absolute bottom-4 right-4 p-2 bg-primary text-primary-foreground rounded-full shadow-lg',
            'hover:opacity-90 transition-opacity'
          )}
        >
          <ArrowDown size={16} />
        </button>
      )}
    </div>
  );
}
