import { Play, Pause, SkipBack, SkipForward, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PlaybackControlsProps {
  isPlaying: boolean;
  speed: number;
  onPlay: () => void;
  onPause: () => void;
  onSpeedChange: (speed: number) => void;
  onSkipToStart: () => void;
  onSkipToEnd: () => void;
  onStepBack: () => void;
  onStepForward: () => void;
}

const SPEEDS = [1, 2, 4, 8];

export function PlaybackControls({
  isPlaying, speed, onPlay, onPause, onSpeedChange,
  onSkipToStart, onSkipToEnd, onStepBack, onStepForward,
}: PlaybackControlsProps) {
  const btn = 'p-2 rounded hover:bg-background text-muted hover:text-foreground transition-colors';

  return (
    <div className="bg-card border border-border rounded-lg px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-1">
        <button onClick={onSkipToStart} className={btn} title="Start (Home)"><SkipBack size={16} /></button>
        <button onClick={onStepBack} className={btn} title="Prev event (←)"><ChevronsLeft size={16} /></button>
        <button
          onClick={isPlaying ? onPause : onPlay}
          className="p-2 rounded bg-primary text-primary-foreground hover:opacity-90"
          title="Play/Pause (Space)"
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} />}
        </button>
        <button onClick={onStepForward} className={btn} title="Next event (→)"><ChevronsRight size={16} /></button>
        <button onClick={onSkipToEnd} className={btn} title="End (End)"><SkipForward size={16} /></button>
      </div>
      <div className="flex items-center gap-1">
        <span className="text-xs text-muted mr-2">Speed:</span>
        {SPEEDS.map(s => (
          <button
            key={s}
            onClick={() => onSpeedChange(s)}
            className={cn(
              'px-2 py-1 rounded text-xs font-medium transition-colors',
              speed === s ? 'bg-primary text-primary-foreground' : 'text-muted hover:text-foreground'
            )}
          >
            {s}x
          </button>
        ))}
      </div>
    </div>
  );
}
