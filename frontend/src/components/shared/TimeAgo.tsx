import { useState, useEffect } from 'react';
import { timeAgo } from '@/lib/utils';

interface Props {
  timestamp: string;
}

export function TimeAgo({ timestamp }: Props) {
  const [display, setDisplay] = useState(() => timeAgo(timestamp));

  useEffect(() => {
    const interval = setInterval(() => {
      setDisplay(timeAgo(timestamp));
    }, 10_000);
    return () => clearInterval(interval);
  }, [timestamp]);

  return <span className="text-xs text-gray-400" title={timestamp}>{display}</span>;
}
