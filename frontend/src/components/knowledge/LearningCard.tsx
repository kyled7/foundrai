import type { Learning } from '@/lib/types';
import { Lightbulb, AlertTriangle, Bug, Sparkles, Pin, Edit, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LearningCardProps {
  learning: Learning;
  onEdit?: (learning: Learning) => void;
  onDelete?: (learning: Learning) => void;
  onPin?: (learning: Learning) => void;
  className?: string;
}

const CATEGORY_STYLES: Record<string, { icon: typeof Lightbulb; color: string; bgColor: string }> = {
  insight: {
    icon: Lightbulb,
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800'
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-amber-400',
    bgColor: 'bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800'
  },
  bug: {
    icon: Bug,
    color: 'text-red-400',
    bgColor: 'bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800'
  },
  improvement: {
    icon: Sparkles,
    color: 'text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800'
  },
};

export function LearningCard({ learning, onEdit, onDelete, onPin, className }: LearningCardProps) {
  const style = CATEGORY_STYLES[learning.category] ?? CATEGORY_STYLES.insight;
  const Icon = style.icon;

  return (
    <div
      className={cn(
        'rounded-lg p-4 border transition-colors',
        learning.pinned ? style.bgColor : 'bg-card border-border',
        className
      )}
    >
      <div className="flex items-start gap-3">
        <Icon size={18} className={cn('shrink-0 mt-0.5', style.color)} />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-foreground mb-2">{learning.content}</p>

          <div className="flex items-center gap-2 flex-wrap">
            <span className={cn('text-[10px] px-1.5 py-0.5 rounded uppercase font-medium', style.color, 'bg-current/10')}>
              {learning.category}
            </span>
            <span className="text-[10px] text-muted">
              {new Date(learning.created_at).toLocaleDateString()}
            </span>
            {learning.pinned && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 font-medium">
                PINNED
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {onPin && (
            <button
              onClick={() => onPin(learning)}
              className={cn(
                'p-1.5 rounded hover:bg-background/50 transition-colors',
                learning.pinned ? 'text-purple-500' : 'text-muted hover:text-foreground'
              )}
              title={learning.pinned ? 'Unpin' : 'Pin'}
            >
              <Pin size={14} className={learning.pinned ? 'fill-current' : ''} />
            </button>
          )}
          {onEdit && (
            <button
              onClick={() => onEdit(learning)}
              className="p-1.5 rounded hover:bg-background/50 text-muted hover:text-foreground transition-colors"
              title="Edit"
            >
              <Edit size={14} />
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(learning)}
              className="p-1.5 rounded hover:bg-background/50 text-muted hover:text-red-500 transition-colors"
              title="Delete"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
