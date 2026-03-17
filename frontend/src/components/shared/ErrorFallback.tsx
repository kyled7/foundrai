import { AlertTriangle, Home, RotateCcw } from 'lucide-react';

interface ErrorFallbackProps {
  error: Error;
  resetError: () => void;
}

export function ErrorFallback({ error, resetError }: ErrorFallbackProps) {
  return (
    <div role="alert" className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
      <AlertTriangle size={48} className="text-warning mb-4" />
      <h2 className="text-xl font-semibold text-foreground mb-2">Something went wrong</h2>
      <p className="text-sm text-muted mb-6 max-w-md">{error.message}</p>
      <div className="flex gap-3">
        <button
          onClick={resetError}
          className="flex items-center gap-2 px-4 py-2 border border-border text-foreground rounded-md text-sm hover:bg-border/50"
        >
          <RotateCcw size={14} />
          Try Again
        </button>
        <a
          href="/"
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm hover:bg-primary/90"
        >
          <Home size={14} />
          Go to Dashboard
        </a>
      </div>
    </div>
  );
}
