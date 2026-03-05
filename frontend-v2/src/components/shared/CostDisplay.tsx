import { formatCost, formatTokens } from '@/lib/utils';

interface CostDisplayProps {
  costUsd: number;
  tokens?: number;
  className?: string;
}

export function CostDisplay({ costUsd, tokens, className }: CostDisplayProps) {
  return (
    <span className={className}>
      <span className="font-medium text-foreground">{formatCost(costUsd)}</span>
      {tokens !== undefined && (
        <span className="text-muted text-xs ml-1">({formatTokens(tokens)} tokens)</span>
      )}
    </span>
  );
}
