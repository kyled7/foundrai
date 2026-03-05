import { useGlobalAnalytics } from '@/hooks/use-analytics';
import { StatCard } from './StatCard';
import { DollarSign, Target, Trophy } from 'lucide-react';

export function GlobalStats() {
  const { data, isLoading } = useGlobalAnalytics();

  if (isLoading || !data) return null;

  const topAgent = data.top_agents?.[0];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <StatCard
        label="Total Spend (All Projects)"
        value={data.total_spend_usd}
        icon={<DollarSign size={18} />}
        format="currency"
      />
      <StatCard
        label="Sprint Success Rate"
        value={data.success_rate}
        icon={<Target size={18} />}
        format="percent"
      />
      <StatCard
        label="Top Agent"
        value={topAgent ? `${topAgent.role} (${topAgent.tasks_completed})` : 'N/A'}
        icon={<Trophy size={18} />}
      />
    </div>
  );
}
