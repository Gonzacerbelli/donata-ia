import { useMemo } from "react";
import { Link } from "react-router-dom";

import { DataTable, type Column } from "@/components/common/DataTable";
import { ExportButtons } from "@/components/common/ExportButtons";
import { PageHeader } from "@/components/common/PageHeader";
import { SearchInput } from "@/components/common/SearchInput";
import { Button } from "@/components/ui/Button";
import { useClients } from "@/features/clients/hooks";
import { useUrlFilters } from "@/hooks/useUrlFilters";
import { formatCurrency, formatDate } from "@/lib/format";
import type { Sale } from "@/types/domain";

import { useSales } from "../hooks";
import { PaymentBadge, StatusBadge } from "./StatusBadge";

export function OrdersPage() {
  const { get, setParam } = useUrlFilters();
  const status = get("status");
  const clientId = get("client");
  const dateFrom = get("from");
  const dateTo = get("to");
  const search = get("search");

  const { data, isLoading, error, refetch } = useSales({
    status,
    client_id: clientId,
    date_from: dateFrom,
    date_to: dateTo,
    search,
  });
  const { data: clients } = useClients();

  const clientNames = useMemo(() => {
    const map = new Map<string, string>();
    for (const client of clients ?? []) map.set(client.id, client.name);
    return map;
  }, [clients]);

  const columns: Column<Sale>[] = [
    { key: "date", header: "Fecha", render: (row) => formatDate(row.date) },
    {
      key: "client",
      header: "Cliente",
      render: (row) => clientNames.get(row.client_id) ?? "—",
    },
    { key: "total", header: "Total", render: (row) => formatCurrency(row.total) },
    { key: "paid", header: "Pagado", render: (row) => formatCurrency(row.paid) },
    {
      key: "balance",
      header: "Saldo",
      render: (row) => (
        <span className={row.balance > 0 ? "text-red-600" : "text-slate-500"}>
          {formatCurrency(row.balance)}
        </span>
      ),
    },
    { key: "status", header: "Estado", render: (row) => <StatusBadge status={row.status} /> },
    { key: "payment", header: "Cobro", render: (row) => <PaymentBadge sale={row} /> },
    {
      key: "actions",
      header: "",
      className: "text-right",
      render: (row) => (
        <Link to={`/ordenes/${row.id}`} className="text-sm font-medium text-brand-600 hover:underline">
          Ver
        </Link>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Órdenes"
        description="Órdenes, pagos y estados."
        actions={
          <Link to="/ordenes/nueva">
            <Button>Nueva orden</Button>
          </Link>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <SearchInput value={search} onChange={(value) => setParam("search", value)} placeholder="Cliente o ítem…" />
        <select
          value={status}
          onChange={(event) => setParam("status", event.target.value)}
          className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-700 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
        >
          <option value="">Todos los estados</option>
          <option value="pendiente">Pendiente</option>
          <option value="en_proceso">En proceso</option>
          <option value="entregado">Entregado</option>
          <option value="cancelado">Cancelado</option>
        </select>
        <select
          value={clientId}
          onChange={(event) => setParam("client", event.target.value)}
          className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-700 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
        >
          <option value="">Todos los clientes</option>
          {(clients ?? []).map((client) => (
            <option key={client.id} value={client.id}>
              {client.name}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={dateFrom}
          onChange={(event) => setParam("from", event.target.value)}
          className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-700 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(event) => setParam("to", event.target.value)}
          className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-700 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
        />
        <ExportButtons
          entity="sales"
          disabled={(data ?? []).length === 0}
          params={{
            status: status || undefined,
            client_id: clientId || undefined,
            date_from: dateFrom || undefined,
            date_to: dateTo || undefined,
            search: search || undefined,
          }}
        />
      </div>

      <DataTable
        columns={columns}
        rows={data ?? []}
        getRowId={(row) => row.id}
        isLoading={isLoading}
        error={error}
        onRetry={() => refetch()}
        emptyTitle="No hay órdenes"
        emptyDescription="Creá la primera orden para empezar a registrar ventas."
        emptyAction={
          <Link to="/ordenes/nueva">
            <Button size="sm">Nueva orden</Button>
          </Link>
        }
      />
    </div>
  );
}