import { useRef } from 'react';
import { cn } from '@/lib/utils';

interface TimelineScrubberProps {
  currentTime: number;
  duration: number;
  eventMarkers: { offset: number; type: string }[];
  onSeek: (time: number) => void;
}

function formatTime(ms: number): string {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  const h = Math.floor(m / 60);
  const pad = (n: number) => String(n).padStart(2, '0');
  return h > 0 ? `${h}:${pad(m % 60)}:${pad(s % 60)}` : `${pad(m)}:${pad(s % 60)}`;
}

function markerColor(type: string): string {
  if (type.includes('completed')) return 'bg-green-400';
  if (type.includes('failed')) return 'bg-red-400';
  if (type.includes('approval')) return 'bg-yellow-400';
  return 'bg-blue-400';
}

export function TimelineScrubber({ currentTime, duration, eventMarkers, onSeek }: TimelineScrubberProps) {
  const trackRef = useRef<HTMLDivElement>(null);

  const pct = duration > 0 ? (currentTime / duration) * 100 : 0;

  const handleClick = (e: React.MouseEvent) => {
    const rect = trackRef.current?.getBoundingClientRect();
    if (!rect) return;
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    onSeek(ratio * duration);
  };

  return (
    <div className="bg-card border border-border rounded-lg px-4 py-3">
      <div className="flex items-center gap-3">
        <span className="text-xs text-muted font-mono w-16 text-right">{formatTime(currentTime)}</span>
        <div ref={trackRef} onClick={handleClick} className="flex-1 relative h-6 cursor-pointer group">
          {/* Track */}
          <div className="absolute top-1/2 -translate-y-1/2 w-full h-1.5 bg-border rounded-full">
            <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${pct}%` }} />
          </div>
          {/* Markers */}
          {eventMarkers.map((m, i) => {
            const left = duration > 0 ? (m.offset / duration) * 100 : 0;
            return (
              <div
                key={i}
                className={cn('absolute top-1/2 -translate-y-1/2 w-1 h-3 rounded-full', markerColor(m.type))}
                style={{ left: `${left}%` }}
              />
            );
          })}
          {/* Thumb */}
          <div
            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-primary rounded-full shadow-md border-2 border-primary-foreground transition-all"
            style={{ left: `${pct}%`, transform: 'translate(-50%, -50%)' }}
          />
        </div>
        <span className="text-xs text-muted font-mono w-16">{formatTime(duration)}</span>
      </div>
    </div>
  );
}
