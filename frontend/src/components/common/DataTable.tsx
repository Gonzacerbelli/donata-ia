import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  getRowId: (row: T) => string;
  isLoading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyAction?: React.ReactNode;
}

export function DataTable<T>({
  columns,
  rows,
  getRowId,
  isLoading = false,
  error = null,
  onRetry,
  emptyTitle = "Sin resultados",
  emptyDescription,
  emptyAction,
}: DataTableProps<T>) {
  if (isLoading) {
    return (
      <div className="flex justify-center rounded-xl border border-slate-200 bg-white py-16">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-red-200 bg-white py-16">
        <p className="text-sm text-red-600">{error.message}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="text-sm font-medium text-brand-600 hover:underline"
          >
            Reintentar
          </button>
        )}
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-xl border border-slate-200 bg-white py-16 text-center">
        <p className="text-sm font-medium text-slate-700">{emptyTitle}</p>
        {emptyDescription && <p className="text-sm text-slate-500">{emptyDescription}</p>}
        {emptyAction}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={cn(
                  "px-4 py-3 text-left font-medium text-slate-500",
                  column.className,
                )}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row) => (
            <tr key={getRowId(row)} className="hover:bg-slate-50">
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={cn("px-4 py-3 text-slate-700", column.className)}
                >
                  {column.render ? column.render(row) : String((row as never)[column.key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}