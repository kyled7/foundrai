import { useRef, useEffect, useState, useCallback } from 'react';
import { FixedSizeList as List } from 'react-window';
import { useEventStore } from '../../stores/eventStore';
import { FeedFilters } from './FeedFilters';
import { FeedEntry } from './FeedEntry';

export function AgentFeed() {
  const filteredEvents = useEventStore((s) => s.filteredEvents());
  const listRef = useRef<List>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [listHeight, setListHeight] = useState(600);

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

  if (filteredEvents.length === 0) {
    return (
      <div className="flex flex-col h-full relative" aria-label="Agent activity feed">
        <FeedFilters />
        <div className="flex-1 overflow-y-auto p-4">
          <p className="text-center text-gray-400 mt-8">No events yet. Activity will appear here as agents work.</p>
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
          className="absolute bottom-4 right-4 bg-blue-600 text-white rounded-full px-3 py-2 shadow-lg text-sm"
        >
          ↓ New activity
        </button>
      )}
    </div>
  );
}
