import { useState } from 'react';
import { useParams } from '@tanstack/react-router';
import { useSprints } from '@/hooks/use-sprints';
import { SprintLauncher } from '@/components/sprint/SprintLauncher';
import { CommandCenter } from '@/components/sprint/CommandCenter';

export function SprintCommandCenter() {
  const { projectId } = useParams({ strict: false }) as { projectId: string };
  const { data: sprintsData } = useSprints(projectId);
  const [activeSprintId, setActiveSprintId] = useState<string | null>(null);

  // Find active sprint from list or use manually set one
  const activeSprint = sprintsData?.sprints?.find(
    s => s.status === 'in_progress' || s.status === 'planning' || s.status === 'created'
  );
  const sprintId = activeSprintId ?? activeSprint?.sprint_id ?? null;

  if (sprintId) {
    return (
      <div data-tutorial="view-results">
        <CommandCenter projectId={projectId} sprintId={sprintId} />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-foreground mb-2">Sprint Command Center</h1>
      <p className="text-muted text-sm mb-6">Define your goal and watch your AI team build it.</p>
      <div data-tutorial="start-sprint">
        <SprintLauncher projectId={projectId} onSprintStarted={setActiveSprintId} />
      </div>
    </div>
  );
}
