import { Spinner } from "@/components/ui/Spinner";
import { formatCurrency, formatDate } from "@/lib/format";
import type { Client } from "@/types/domain";

import { useClientSales } from "../hooks";

export function ClientSummary({ client }: { client: Client }) {
  const { data, isLoading, error } = useClientSales(client.id);

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return <p className="py-4 text-sm text-red-600">{error.message}</p>;
  }

  const sales = data ?? [];
  const billed = sales.reduce((sum, sale) => sum + sale.total, 0);
  const balance = sales.reduce((sum, sale) => sum + sale.balance, 0);

  const stats = [
    { label: "Órdenes", value: String(sales.length) },
    { label: "Facturado", value: formatCurrency(billed) },
    { label: "Saldo pendiente", value: formatCurrency(balance) },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-3">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-lg border border-slate-200 p-3">
            <p className="text-xs text-slate-500">{stat.label}</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{stat.value}</p>
          </div>
        ))}
      </div>

      {sales.length === 0 ? (
        <p className="text-sm text-slate-500">Este cliente todavía no tiene órdenes.</p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {sales.slice(0, 8).map((sale) => (
            <li key={sale.id} className="flex items-center justify-between py-2 text-sm">
              <span className="text-slate-600">{formatDate(sale.date)}</span>
              <span className="text-slate-800">{formatCurrency(sale.total)}</span>
              <span className={sale.balance > 0 ? "text-amber-600" : "text-emerald-600"}>
                {sale.balance > 0 ? `Debe ${formatCurrency(sale.balance)}` : "Pagada"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}