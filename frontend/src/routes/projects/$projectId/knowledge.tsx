import { useParams } from '@tanstack/react-router';
import { KnowledgeBasePage } from '@/components/knowledge/KnowledgeBasePage';

export function ProjectKnowledgeBasePage() {
  const { projectId } = useParams({ strict: false }) as { projectId: string };

  return <KnowledgeBasePage projectId={projectId} />;
}
