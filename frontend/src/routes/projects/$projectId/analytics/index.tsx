import { useParams } from '@tanstack/react-router';
import { ProjectAnalyticsPage } from '@/components/analytics/AnalyticsPage';

export function AnalyticsPage() {
  const { projectId } = useParams({ strict: false }) as { projectId: string };
  return <ProjectAnalyticsPage projectId={projectId} />;
}
