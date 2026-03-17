import type { Learning } from '@/lib/types';
import { Lightbulb, AlertTriangle, Bug, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LearningsTimelineProps {
  learnings: Learning[];
}

const CATEGORY_STYLES: Record<string, { icon: typeof Lightbulb; color: string }> = {
  insight: { icon: Lightbulb, color: 'text-yellow-400' },
  warning: { icon: AlertTriangle, color: 'text-amber-400' },
  bug: { icon: Bug, color: 'text-red-400' },
  improvement: { icon: Sparkles, color: 'text-blue-400' },
};

export function LearningsTimeline({ learnings }: LearningsTimelineProps) {
  if (learnings.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 text-center text-muted text-sm">
        No learnings captured yet
      </div>
    );
  }

  // Group by sprint_id
  const grouped = new Map<string, Learning[]>();
  for (const l of learnings) {
    const key = l.sprint_id;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key)!.push(l);
  }

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium text-foreground mb-4">Learnings Timeline</h3>
      <div className="space-y-6">
        {Array.from(grouped.entries()).map(([sprintId, items]) => (
          <div key={sprintId}>
            <p className="text-xs text-muted font-medium mb-2">Sprint {sprintId.slice(0, 8)}</p>
            <div className="border-l-2 border-border pl-4 space-y-3">
              {items.map(item => {
                const style = CATEGORY_STYLES[item.category] ?? CATEGORY_STYLES.insight;
                const Icon = style.icon;
                return (
                  <div key={item.learning_id} className="flex gap-3">
                    <Icon size={14} className={cn('shrink-0 mt-0.5', style.color)} />
                    <div className="min-w-0">
                      <p className="text-sm text-foreground">{item.content}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={cn('text-[10px] px-1.5 py-0.5 rounded', style.color, 'bg-current/10')}>
                          {item.category}
                        </span>
                        <span className="text-[10px] text-muted">
                          {new Date(item.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
