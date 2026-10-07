export function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-slate-200 ${className ?? ""}`} />;
}

export function TableSkeleton({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="space-y-2" aria-hidden="true">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }).map((__, columnIndex) => (
            <Skeleton key={columnIndex} className="h-8 w-full" />
          ))}
        </div>
      ))}
    </div>
  );
}