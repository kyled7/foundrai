interface PageSkeletonProps {
  layout: 'cards' | 'table' | 'detail' | 'form' | 'analytics';
}

function Shimmer({ className }: { className: string }) {
  return <div className={`animate-pulse bg-border/50 rounded ${className}`} />;
}

function CardsSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="p-4 border border-border rounded-lg space-y-3">
          <Shimmer className="h-4 w-3/4" />
          <Shimmer className="h-3 w-full" />
          <Shimmer className="h-3 w-1/2" />
        </div>
      ))}
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-3">
      <Shimmer className="h-10 w-full" />
      {Array.from({ length: 5 }).map((_, i) => (
        <Shimmer key={i} className="h-12 w-full" />
      ))}
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <Shimmer className="h-8 w-1/3" />
      <Shimmer className="h-4 w-2/3" />
      <div className="grid grid-cols-2 gap-4">
        <Shimmer className="h-32" />
        <Shimmer className="h-32" />
      </div>
    </div>
  );
}

function FormSkeleton() {
  return (
    <div className="space-y-6 max-w-md">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Shimmer className="h-3 w-24" />
          <Shimmer className="h-10 w-full" />
        </div>
      ))}
    </div>
  );
}

function AnalyticsSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Shimmer key={i} className="h-24" />
        ))}
      </div>
      <Shimmer className="h-64" />
    </div>
  );
}

const layouts = { cards: CardsSkeleton, table: TableSkeleton, detail: DetailSkeleton, form: FormSkeleton, analytics: AnalyticsSkeleton };

export function PageSkeleton({ layout }: PageSkeletonProps) {
  const Layout = layouts[layout];
  return (
    <div className="p-6" aria-hidden="true">
      <Layout />
    </div>
  );
}
