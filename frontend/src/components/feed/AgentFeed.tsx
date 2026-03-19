import { useRef, useEffect, useState, useCallback } from 'react';
import { FixedSizeList as List } from 'react-window';
import { useEventStore } from '../../stores/eventStore';
import { ErrorBoundary } from '../shared/ErrorBoundary';
import { FeedFilters } from './FeedFilters';
import { FeedEntry } from './FeedEntry';

function FeedSkeleton() {
  return (
    <div className="p-4 space-y-4">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 animate-pulse"
        >
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full flex-shrink-0" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function AgentFeedContent() {
  const filteredEvents = useEventStore((s) => s.filteredEvents());
  const allEvents = useEventStore((s) => s.events);
  const listRef = useRef<List>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [listHeight, setListHeight] = useState(600);
  const [loading, setLoading] = useState(true);

  // Show loading state for first 2 seconds or until first event arrives
  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 2000);
    if (allEvents.length > 0) {
      setLoading(false);
    }
    return () => clearTimeout(timer);
  }, [allEvents.length]);

  // Update list height based on container size
  useEffect(() => {
    const updateHeight = () => {
      if (containerRef.current) {
        const height = containerRef.current.clientHeight;
        setListHeight(height);
      }
    };

    updateHeight();
    window.addEventListener('resize', updateHeight);
    return () => window.removeEventListener('resize', updateHeight);
  }, []);

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (autoScroll && filteredEvents.length > 0 && listRef.current) {
      listRef.current.scrollToItem(filteredEvents.length - 1, 'end');
    }
  }, [filteredEvents.length, autoScroll]);

  const handleScroll = useCallback(({ scrollOffset, scrollUpdateWasRequested }: { scrollOffset: number; scrollUpdateWasRequested: boolean }) => {
    if (!scrollUpdateWasRequested && listRef.current) {
      const totalHeight = filteredEvents.length * 120;
      const visibleHeight = listHeight;
      const maxScroll = totalHeight - visibleHeight;
      const atBottom = maxScroll - scrollOffset < 50;
      setAutoScroll(atBottom);
    }
  }, [filteredEvents.length, listHeight]);

  const scrollToBottom = useCallback(() => {
    setAutoScroll(true);
    if (listRef.current && filteredEvents.length > 0) {
      listRef.current.scrollToItem(filteredEvents.length - 1, 'end');
    }
  }, [filteredEvents.length]);

  const Row = useCallback(({ index, style }: { index: number; style: React.CSSProperties }) => {
    const event = filteredEvents[index];
    return (
      <div style={style} className="px-4">
        <FeedEntry event={event} />
      </div>
    );
  }, [filteredEvents]);

  if (loading) {
    return (
      <div className="flex flex-col h-full relative" aria-label="Agent activity feed">
        <FeedFilters />
        <div className="flex-1 overflow-y-auto">
          <FeedSkeleton />
        </div>
      </div>
    );
  }

  if (filteredEvents.length === 0) {
    return (
      <div className="flex flex-col h-full relative" aria-label="Agent activity feed">
        <FeedFilters />
        <div className="flex-1 overflow-y-auto p-4">
          <p className="text-center text-gray-500 dark:text-gray-400 mt-8">No events yet. Activity will appear here as agents work.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full relative" aria-label="Agent activity feed">
      <FeedFilters />
      <div ref={containerRef} className="flex-1" aria-live="polite">
        <List
          ref={listRef}
          height={listHeight}
          itemCount={filteredEvents.length}
          itemSize={120}
          width="100%"
          onScroll={handleScroll}
        >
          {Row}
        </List>
      </div>
      {!autoScroll && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-4 right-4 bg-blue-600 hover:bg-blue-700 text-white rounded-full px-3 py-2 shadow-lg text-sm transition-colors"
        >
          ↓ New activity
        </button>
      )}
    </div>
  );
}

export function AgentFeed() {
  return (
    <ErrorBoundary>
      <AgentFeedContent />
    </ErrorBoundary>
  );
}
