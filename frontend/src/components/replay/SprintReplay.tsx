import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useReplayEvents } from '@/hooks/use-analytics';
import { ActivityFeed } from '@/components/sprint/ActivityFeed';
import { TimelineScrubber } from './TimelineScrubber';
import { PlaybackControls } from './PlaybackControls';
import { PageSkeleton } from '@/components/shared/LoadingSkeleton';
import type { WSEvent } from '@/lib/types';

interface SprintReplayProps {
  sprintId: string;
}

export function SprintReplay({ sprintId }: SprintReplayProps) {
  const { data, isLoading } = useReplayEvents(sprintId);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const lastFrameRef = useRef<number>(0);
  const rafRef = useRef<number>(0);

  // Convert events to WSEvent format with offsets
  const { wsEvents, offsets, duration } = useMemo(() => {
    const events = data?.events ?? [];
    if (events.length === 0) return { wsEvents: [] as WSEvent[], offsets: [] as number[], duration: 0 };

    const startTime = new Date(events[0].timestamp).getTime();
    const offs = events.map(e => new Date(e.timestamp).getTime() - startTime);
    const dur = offs.length > 0 ? offs[offs.length - 1] + 1000 : 0;

    const ws: WSEvent[] = events.map((e, i) => ({
      type: e.event_type as WSEvent['type'],
      data: e.data,
      timestamp: e.timestamp,
      sequence: i,
    }));

    return { wsEvents: ws, offsets: offs, duration: dur };
  }, [data]);

  // Visible events based on current time
  const visibleEvents = useMemo(() => {
    const idx = offsets.findIndex(o => o > currentTime);
    const count = idx === -1 ? wsEvents.length : idx;
    return wsEvents.slice(0, count);
  }, [wsEvents, offsets, currentTime]);

  // Event markers for scrubber
  const eventMarkers = useMemo(() =>
    wsEvents.map((e, i) => ({ offset: offsets[i], type: e.type })),
    [wsEvents, offsets]
  );

  // rAF playback loop
  const tick = useCallback((timestamp: number) => {
    if (lastFrameRef.current === 0) lastFrameRef.current = timestamp;
    const delta = (timestamp - lastFrameRef.current) * speed;
    lastFrameRef.current = timestamp;

    setCurrentTime(prev => {
      const next = prev + delta;
      if (next >= duration) {
        setIsPlaying(false);
        return duration;
      }
      return next;
    });

    rafRef.current = requestAnimationFrame(tick);
  }, [speed, duration]);

  useEffect(() => {
    if (isPlaying) {
      lastFrameRef.current = 0;
      rafRef.current = requestAnimationFrame(tick);
    } else {
      cancelAnimationFrame(rafRef.current);
    }
    return () => cancelAnimationFrame(rafRef.current);
  }, [isPlaying, tick]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.code === 'Space') { e.preventDefault(); setIsPlaying(p => !p); }
      if (e.code === 'ArrowLeft') stepBack();
      if (e.code === 'ArrowRight') stepForward();
      if (e.key >= '1' && e.key <= '4') setSpeed([1, 2, 4, 8][Number(e.key) - 1]);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  });

  const stepBack = () => {
    let idx = -1;
    for (let i = offsets.length - 1; i >= 0; i--) {
      if (offsets[i] < currentTime) { idx = i; break; }
    }
    if (idx >= 0) setCurrentTime(offsets[idx]);
  };

  const stepForward = () => {
    const idx = offsets.findIndex(o => o > currentTime);
    if (idx >= 0) setCurrentTime(offsets[idx]);
  };

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 min-h-0">
        <ActivityFeed events={visibleEvents} />
      </div>
      <div className="p-4 space-y-2">
        <TimelineScrubber
          currentTime={currentTime}
          duration={duration}
          eventMarkers={eventMarkers}
          onSeek={t => { setCurrentTime(t); setIsPlaying(false); }}
        />
        <PlaybackControls
          isPlaying={isPlaying}
          speed={speed}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onSpeedChange={setSpeed}
          onSkipToStart={() => { setCurrentTime(0); setIsPlaying(false); }}
          onSkipToEnd={() => { setCurrentTime(duration); setIsPlaying(false); }}
          onStepBack={stepBack}
          onStepForward={stepForward}
        />
      </div>
    </div>
  );
}
