import { useParams } from '@tanstack/react-router';
import { SprintReplay } from '@/components/replay/SprintReplay';

export function SprintReplayPage() {
  const { sprintId } = useParams({ strict: false }) as { sprintId: string };

  return (
    <div className="h-[calc(100vh-4rem)]">
      <SprintReplay sprintId={sprintId} />
    </div>
  );
}
