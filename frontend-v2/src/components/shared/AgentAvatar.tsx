import { cn } from '@/lib/utils';

const roleConfig: Record<string, { icon: string; color: string }> = {
  product_manager: { icon: '📋', color: 'bg-blue-500/20' },
  developer: { icon: '💻', color: 'bg-green-500/20' },
  qa_engineer: { icon: '🧪', color: 'bg-purple-500/20' },
  architect: { icon: '🏗️', color: 'bg-orange-500/20' },
  designer: { icon: '🎨', color: 'bg-pink-500/20' },
  devops: { icon: '⚙️', color: 'bg-yellow-500/20' },
};

interface AgentAvatarProps {
  role: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeMap = { sm: 'w-6 h-6 text-xs', md: 'w-8 h-8 text-sm', lg: 'w-10 h-10 text-base' };

export function AgentAvatar({ role, size = 'md', className }: AgentAvatarProps) {
  const config = roleConfig[role] ?? { icon: '🤖', color: 'bg-gray-500/20' };
  return (
    <div className={cn('rounded-full flex items-center justify-center', config.color, sizeMap[size], className)}>
      {config.icon}
    </div>
  );
}
