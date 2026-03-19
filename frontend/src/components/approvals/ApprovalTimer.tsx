import { useState, useEffect } from 'react';
import { timeRemaining } from '@/lib/utils';

interface Props {
  expiresAt: string | null;
}

export function ApprovalTimer({ expiresAt }: Props) {
  const [display, setDisplay] = useState(() => expiresAt ? timeRemaining(expiresAt) : null);

  useEffect(() => {
    if (!expiresAt) return;

    const interval = setInterval(() => {
      setDisplay(timeRemaining(expiresAt));
    }, 1000);

    return () => clearInterval(interval);
  }, [expiresAt]);

  if (!expiresAt || display === 'expired') return null;

  return (
    <span className="text-xs text-amber-600 dark:text-amber-400" title={`Expires at ${expiresAt}`}>
      {display} remaining
    </span>
  );
}
