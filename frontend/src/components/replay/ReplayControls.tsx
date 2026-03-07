interface Props {
  isPlaying: boolean;
  speed: number;
  current: number;
  total: number;
  onPlayPause: () => void;
  onSpeedChange: (speed: number) => void;
  onSeek: (index: number) => void;
}

const SPEEDS = [1, 2, 5, 10];

export function ReplayControls({ isPlaying, speed, current, total, onPlayPause, onSpeedChange, onSeek }: Props) {
  return (
    <div className="flex items-center gap-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
      <button
        onClick={onPlayPause}
        aria-label={isPlaying ? 'Pause replay' : 'Play replay'}
        className="w-10 h-10 flex items-center justify-center bg-blue-600 text-white rounded-full hover:bg-blue-700"
      >
        {isPlaying ? '⏸' : '▶'}
      </button>

      <div className="flex gap-1" role="group" aria-label="Playback speed">
        {SPEEDS.map(s => (
          <button
            key={s}
            onClick={() => onSpeedChange(s)}
            aria-label={`Set speed to ${s}x`}
            aria-pressed={speed === s}
            className={`px-2 py-1 text-xs rounded ${speed === s ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'}`}
          >
            {s}x
          </button>
        ))}
      </div>

      <input
        type="range"
        min={0}
        max={Math.max(total - 1, 0)}
        value={current}
        onChange={e => onSeek(Number(e.target.value))}
        className="flex-1"
      />

      <span className="text-sm text-gray-500 whitespace-nowrap">
        {current + 1} / {total}
      </span>
    </div>
  );
}
