import { cn } from '@/lib/utils';

const AGENT_COLORS: Record<string, { bg: string; emoji: string }> = {
  product_manager: { bg: 'bg-purple-500', emoji: '📋' },
  developer:       { bg: 'bg-blue-500',   emoji: '💻' },
  qa_engineer:     { bg: 'bg-green-500',  emoji: '🧪' },
  architect:       { bg: 'bg-amber-500',  emoji: '🏗️' },
  designer:        { bg: 'bg-pink-500',   emoji: '🎨' },
  devops:          { bg: 'bg-indigo-500', emoji: '🚀' },
};

const sizes = {
  xs: 'w-5 h-5 text-xs',
  sm: 'w-6 h-6 text-xs',
  md: 'w-8 h-8 text-sm',
};

interface Props {
  role: string;
  size?: 'xs' | 'sm' | 'md';
}

export function AgentAvatar({ role, size = 'md' }: Props) {
  const config = AGENT_COLORS[role] ?? AGENT_COLORS.developer;

  return (
    <div
      className={cn(
        'rounded-full flex items-center justify-center text-white',
        config.bg,
        sizes[size]
      )}
      title={role.replace('_', ' ')}
    >
      {config.emoji}
    </div>
  );
}
