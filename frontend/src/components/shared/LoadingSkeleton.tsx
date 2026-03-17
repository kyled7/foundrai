import { cn } from '@/lib/utils';

interface LoadingSkeletonProps {
  className?: string;
}

export function LoadingSkeleton({ className }: LoadingSkeletonProps) {
  return <div className={cn('animate-pulse bg-border rounded', className)} />;
}

export function CardSkeleton() {
  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-3">
      <LoadingSkeleton className="h-5 w-2/3" />
      <LoadingSkeleton className="h-4 w-full" />
      <LoadingSkeleton className="h-4 w-1/2" />
    </div>
  );
}

export function PageSkeleton() {
  return (
    <div className="space-y-6 p-6">
      <LoadingSkeleton className="h-8 w-48" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  );
}
