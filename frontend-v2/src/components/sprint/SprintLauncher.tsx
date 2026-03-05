import { useState, useCallback } from 'react';
import { useCreateSprint } from '@/hooks/use-sprints';
import { api } from '@/lib/api';
import { Rocket, ChevronDown } from 'lucide-react';

interface SprintLauncherProps {
  projectId: string;
  onSprintStarted: (sprintId: string) => void;
}

export function SprintLauncher({ projectId, onSprintStarted }: SprintLauncherProps) {
  const [goal, setGoal] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const createSprint = useCreateSprint(projectId);

  const handleStart = useCallback(async () => {
    if (!goal.trim() || isStarting) return;
    setIsStarting(true);
    try {
      const sprint = await createSprint.mutateAsync({ goal: goal.trim() });
      // Try to start the sprint (may fail if backend doesn't support it yet)
      try {
        await api.sprints.start(sprint.sprint_id);
      } catch {
        // Sprint created but start endpoint not available — that's ok
      }
      onSprintStarted(sprint.sprint_id);
    } catch {
      setIsStarting(false);
    }
  }, [goal, isStarting, createSprint, onSprintStarted]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleStart();
    }
  };

  return (
    <div className="bg-card border border-border rounded-xl p-6 space-y-4">
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">Sprint Goal</label>
        <textarea
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={3}
          placeholder="Describe what you want to build..."
          className="w-full bg-background border border-border rounded-lg px-4 py-3 text-foreground placeholder:text-muted resize-none focus:outline-none focus:ring-2 focus:ring-primary/50 text-sm"
          autoFocus
        />
        <p className="text-xs text-muted mt-1">Press Ctrl+Enter to start</p>
      </div>

      {/* Advanced options */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="flex items-center gap-1 text-xs text-muted hover:text-foreground"
      >
        <ChevronDown size={12} className={showAdvanced ? 'rotate-180' : ''} />
        Advanced options
      </button>

      {showAdvanced && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div>
            <label className="text-xs text-muted block mb-1">Model override</label>
            <select className="w-full bg-background border border-border rounded-md px-2 py-1.5 text-xs text-foreground">
              <option value="">Default</option>
              <option value="claude-opus-4">claude-opus-4</option>
              <option value="claude-sonnet-4">claude-sonnet-4</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-muted block mb-1">Budget</label>
            <input type="number" defaultValue={5} className="w-full bg-background border border-border rounded-md px-2 py-1.5 text-xs text-foreground" />
          </div>
          <div>
            <label className="text-xs text-muted block mb-1">Parallel tasks</label>
            <input type="number" defaultValue={3} className="w-full bg-background border border-border rounded-md px-2 py-1.5 text-xs text-foreground" />
          </div>
        </div>
      )}

      <button
        onClick={handleStart}
        disabled={!goal.trim() || isStarting}
        className="flex items-center justify-center gap-2 w-full px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
      >
        <Rocket size={18} />
        {isStarting ? 'Starting Sprint...' : 'Start Sprint'}
      </button>
    </div>
  );
}
