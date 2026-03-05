import { timeAgo } from '@/lib/utils';

interface TimeAgoProps {
  date: string | Date;
  className?: string;
}

export function TimeAgo({ date, className }: TimeAgoProps) {
  return <time className={className} title={new Date(date).toLocaleString()}>{timeAgo(date)}</time>;
}
