import { useParams } from 'react-router-dom';
import { ReplayView } from '../components/replay/ReplayView';

export function ReplayPage() {
  const { sprintId } = useParams<{ sprintId: string }>();

  if (!sprintId) {
    return <p className="p-6 text-gray-400">No sprint ID provided.</p>;
  }

  return (
    <div className="p-6 h-full flex flex-col">
      <h1 className="text-xl font-bold mb-4">🎬 Sprint Replay</h1>
      <div className="flex-1 min-h-0">
        <ReplayView sprintId={sprintId} />
      </div>
    </div>
  );
}
