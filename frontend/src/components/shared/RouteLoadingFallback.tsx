import { Loader2 } from 'lucide-react';

interface RouteLoadingFallbackProps {
  message?: string;
}

export function RouteLoadingFallback({ message = 'Loading...' }: RouteLoadingFallbackProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] gap-3" aria-busy="true">
      <Loader2 size={32} className="text-primary animate-spin" />
      <p className="text-sm text-muted">{message}</p>
    </div>
  );
}
