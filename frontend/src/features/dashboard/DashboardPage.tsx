import { useNavigate } from "react-router-dom";

import { ErrorState } from "@/components/common/ErrorState";
import { PageHeader } from "@/components/common/PageHeader";
import { Skeleton } from "@/components/common/Skeleton";
import { useUrlFilters } from "@/hooks/useUrlFilters";
import { formatCurrency } from "@/lib/format";

import { useInventoryValue, useLowStock, useSalesSummary, useTopProducts } from "./hooks";

export function DashboardPage() {
  const navigate = useNavigate();
  const { get, setParam } = useUrlFilters();
  const from = get("from");
  const to = get("to");
  const range = { date_from: from || undefined, date_to: to || undefined };

  const summary = useSalesSummary(range);
  const topProducts = useTopProducts(range);
  const lowStock = useLowStock();
  const inventory = useInventoryValue();

  const rangeQuery = new URLSearchParams();
  if (from) rangeQuery.set("from", from);
  if (to) rangeQuery.set("to", to);
  const rangeSuffix = rangeQuery.toString();

  function goTo(path: string, extra?: Record<string, string>) {
    const query = new URLSearchParams(rangeSuffix);
    for (const [key, value] of Object.entries(extra ?? {})) query.set(key, value);
    const suffix = query.toString();
    navigate(suffix ? `${path}?${suffix}` : path);
  }

  return (
    <div>
      <PageHeader title="Dashboard" description="Resumen de la operación en el período elegido." />

      <div className="mb-6 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-sm text-slate-600">
          Desde
          <input
            type="date"
            value={from}
            onChange={(event) => setParam("from", event.target.value)}
            className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-900 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-slate-600">
          Hasta
          <input
            type="date"
            value={to}
            onChange={(event) => setParam("to", event.target.value)}
            className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-900 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
          />
        </label>
        {(from || to) && (
          <button
            type="button"
            className="text-sm font-medium text-brand-600 hover:underline"
            onClick={() => {
              setParam("from", "");
              setParam("to", "");
            }}
          >
            Limpiar
          </button>
        )}
      </div>

      {summary.error ? (
        <ErrorState message={summary.error.message} onRetry={() => summary.refetch()} />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Kpi
            title="Ventas"
            value={summary.data ? formatCurrency(summary.data.revenue) : undefined}
            isLoading={summary.isLoading}
            onClick={() => goTo("/ordenes")}
          />
          <Kpi
            title="Órdenes"
            value={summary.data ? String(summary.data.sales_count) : undefined}
            isLoading={summary.isLoading}
            onClick={() => goTo("/ordenes")}
          />
          <Kpi
            title="Cobrado"
            value={summary.data ? formatCurrency(summary.data.collected) : undefined}
            isLoading={summary.isLoading}
            onClick={() => goTo("/ordenes")}
          />
          <Kpi
            title="Por cobrar"
            value={summary.data ? formatCurrency(summary.data.receivable) : undefined}
            isLoading={summary.isLoading}
            accent="text-amber-600"
            onClick={() => goTo("/ordenes")}
          />
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="rounded-xl border border-slate-200 bg-white p-4 lg:col-span-2">
          <h2 className="mb-3 text-sm font-semibold text-slate-800">Productos más vendidos</h2>
          {topProducts.isLoading ? (
            <div className="flex flex-col gap-2">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : topProducts.error ? (
            <p className="text-sm text-red-600">{topProducts.error.message}</p>
          ) : !topProducts.data || topProducts.data.length === 0 ? (
            <p className="text-sm text-slate-500">Sin ventas en el período.</p>
          ) : (
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase text-slate-400">
                  <th className="pb-2">Producto</th>
                  <th className="pb-2">Cantidad</th>
                  <th className="pb-2 text-right">Facturado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {topProducts.data.map((product) => (
                  <tr key={product.description}>
                    <td className="py-2 text-slate-700">{product.description}</td>
                    <td className="py-2 text-slate-600">{product.qty}</td>
                    <td className="py-2 text-right text-slate-800">{formatCurrency(product.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <div className="flex flex-col gap-4">
          <section className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-2 text-sm font-semibold text-slate-800">Valor de inventario</h2>
            {inventory.isLoading ? (
              <Skeleton className="h-8 w-32" />
            ) : (
              <>
                <p className="text-2xl font-semibold text-slate-900">
                  {formatCurrency(inventory.data?.inventory_value ?? 0)}
                </p>
                <p className="text-xs text-slate-500">{inventory.data?.units ?? 0} unidades</p>
              </>
            )}
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-2 text-sm font-semibold text-slate-800">Stock bajo</h2>
            {lowStock.isLoading ? (
              <Skeleton className="h-8 w-full" />
            ) : (lowStock.data ?? []).length === 0 ? (
              <p className="text-sm text-slate-500">Todo el stock está en niveles saludables.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {(lowStock.data ?? []).slice(0, 6).map((product) => (
                  <li key={product.id} className="flex items-center justify-between text-sm">
                    <span className="text-slate-700">{product.name}</span>
                    <span className={product.stock === 0 ? "text-red-600" : "text-amber-600"}>
                      {product.stock}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            <button
              type="button"
              className="mt-3 text-sm font-medium text-brand-600 hover:underline"
              onClick={() => navigate("/productos")}
            >
              Ver productos
            </button>
          </section>
        </div>
      </div>
    </div>
  );
}

interface KpiProps {
  title: string;
  value?: string;
  accent?: string;
  onClick?: () => void;
  isLoading?: boolean;
}

function Kpi({ title, value, accent, onClick, isLoading = false }: KpiProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex flex-col items-start rounded-xl border border-slate-200 bg-white p-4 text-left transition-colors hover:border-brand-300 hover:bg-brand-50"
    >
      <span className="text-xs font-medium uppercase tracking-wide text-slate-400">{title}</span>
      {isLoading ? (
        <Skeleton className="mt-2 h-7 w-24" />
      ) : (
        <span className={`mt-1 text-2xl font-semibold ${accent ?? "text-slate-900"}`}>{value}</span>
      )}
    </button>
  );
}