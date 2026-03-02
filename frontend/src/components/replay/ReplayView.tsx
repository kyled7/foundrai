import { useEffect, useState, useRef, useCallback } from 'react';
import { ReplayControls } from './ReplayControls';
import { FeedEntry } from '../feed/FeedEntry';
import { getReplayEvents, type ReplayEvent } from '../../api/replay';
import type { WSMessage } from '../../types';

interface Props {
  sprintId: string;
}

export function ReplayView({ sprintId }: Props) {
  const [allEvents, setAllEvents] = useState<ReplayEvent[]>([]);
  const [visibleCount, setVisibleCount] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [loading, setLoading] = useState(true);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    setLoading(true);
    getReplayEvents(sprintId)
      .then(data => {
        setAllEvents(data.events);
        setVisibleCount(0);
      })
      .finally(() => setLoading(false));
  }, [sprintId]);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    stopTimer();
    if (isPlaying && visibleCount < allEvents.length) {
      timerRef.current = setInterval(() => {
        setVisibleCount(prev => {
          if (prev >= allEvents.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1000 / speed);
    }
    return stopTimer;
  }, [isPlaying, speed, allEvents.length, stopTimer]);

  const toWSMessage = (e: ReplayEvent, i: number): WSMessage => ({
    type: e.event_type,
    data: e.data,
    timestamp: e.timestamp,
    sequence: i,
  });

  if (loading) return <p className="text-gray-400 text-center py-8">Loading replay...</p>;
  if (allEvents.length === 0) return <p className="text-gray-400 text-center py-8">No events to replay.</p>;

  return (
    <div className="flex flex-col h-full gap-4">
      <ReplayControls
        isPlaying={isPlaying}
        speed={speed}
        current={visibleCount}
        total={allEvents.length}
        onPlayPause={() => setIsPlaying(!isPlaying)}
        onSpeedChange={setSpeed}
        onSeek={(i) => { setVisibleCount(i); setIsPlaying(false); }}
      />
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {allEvents.slice(0, visibleCount + 1).map((e, i) => (
          <FeedEntry key={e.event_id} event={toWSMessage(e, i)} />
        ))}
      </div>
    </div>
  );
}
