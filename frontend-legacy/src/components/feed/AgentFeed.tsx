import { useEventStore } from '../../stores/eventStore';
import { useAutoScroll } from '../../hooks/useAutoScroll';
import { FeedFilters } from './FeedFilters';
import { FeedEntry } from './FeedEntry';

export function AgentFeed() {
  const filteredEvents = useEventStore((s) => s.filteredEvents());
  const { bottomRef, autoScroll, handleScroll, scrollToBottom } = useAutoScroll([filteredEvents.length]);

  return (
    <div className="flex flex-col h-full relative" aria-label="Agent activity feed">
      <FeedFilters />
      <div
        className="flex-1 overflow-y-auto p-4 space-y-2"
        aria-live="polite"
        onScroll={handleScroll}
      >
        {filteredEvents.length === 0 && (
          <p className="text-center text-gray-400 mt-8">No events yet. Activity will appear here as agents work.</p>
        )}
        {filteredEvents.map((event) => (
          <FeedEntry key={event.sequence} event={event} />
        ))}
        <div ref={bottomRef} />
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
