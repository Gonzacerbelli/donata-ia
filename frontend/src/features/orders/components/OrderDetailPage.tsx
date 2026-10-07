import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { PageHeader } from "@/components/common/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useClients } from "@/features/clients/hooks";
import { ApiError } from "@/lib/http";
import { formatCurrency, formatDate } from "@/lib/format";
import type { PaymentType, SaleStatus } from "@/types/domain";

import { useAddPayment, useDeleteSale, useSale, useUpdateSale } from "../hooks";
import { PaymentBadge, StatusBadge } from "./StatusBadge";

export function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: sale, isLoading, error } = useSale(id);
  const { data: clients } = useClients();
  const updateSale = useUpdateSale(id ?? "");
  const addPayment = useAddPayment(id ?? "");
  const deleteSale = useDeleteSale();

  const [amount, setAmount] = useState("");
  const [paymentType, setPaymentType] = useState<PaymentType>("pago");
  const [method, setMethod] = useState("");
  const [isConfirmingDelete, setConfirmingDelete] = useState(false);

  const clientName = useMemo(
    () => clients?.find((client) => client.id === sale?.client_id)?.name ?? "—",
    [clients, sale],
  );

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner />
      </div>
    );
  }

  if (error || !sale) {
    return (
      <div className="flex flex-col items-center gap-4 py-16">
        <p className="text-sm text-red-600">{error?.message ?? "No encontramos la orden."}</p>
        <Link to="/ordenes">
          <Button variant="secondary">Volver a órdenes</Button>
        </Link>
      </div>
    );
  }

  function handleAddPayment(event: React.FormEvent) {
    event.preventDefault();
    const value = Number(amount);
    if (!value || value <= 0) return;
    addPayment.mutate(
      { amount: value, type: paymentType, method: method.trim() || undefined },
      { onSuccess: () => { setAmount(""); setMethod(""); } },
    );
  }

  function handleDelete() {
    deleteSale.mutate(sale!.id, { onSuccess: () => navigate("/ordenes") });
  }

  return (
    <div>
      <PageHeader
        title={`Orden de ${clientName}`}
        description={`Creada el ${formatDate(sale.date)}`}
        actions={
          <Link to="/ordenes">
            <Button variant="secondary">Volver</Button>
          </Link>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-6 lg:col-span-2">
          <section className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-semibold text-slate-800">Ítems</h2>
            <ul className="divide-y divide-slate-100">
              {sale.items.map((item, index) => (
                <li key={index} className="flex items-center justify-between py-2 text-sm">
                  <span className="text-slate-700">
                    {item.qty} × {item.description ?? "Ítem"}
                  </span>
                  <span className="text-slate-800">
                    {item.unit_price != null ? formatCurrency(item.qty * item.unit_price) : "—"}
                  </span>
                </li>
              ))}
            </ul>
            <dl className="mt-4 flex flex-col gap-1 border-t border-slate-100 pt-3 text-sm">
              <Row label="Subtotal" value={formatCurrency(sale.subtotal)} />
              <Row label="Descuento" value={`-${formatCurrency(sale.discount)}`} />
              <Row label="Envío" value={formatCurrency(sale.shipping_cost)} />
              <Row label="Total" value={formatCurrency(sale.total)} strong />
              <Row label="Pagado" value={formatCurrency(sale.paid)} />
              <Row label="Saldo" value={formatCurrency(sale.balance)} strong />
            </dl>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-semibold text-slate-800">Pagos</h2>
            {sale.payments.length === 0 ? (
              <p className="text-sm text-slate-500">Todavía no hay pagos registrados.</p>
            ) : (
              <ul className="divide-y divide-slate-100">
                {sale.payments.map((payment, index) => (
                  <li key={index} className="flex items-center justify-between py-2 text-sm">
                    <span className="text-slate-600">
                      {formatDate(payment.date)} · {payment.type === "adelanto" ? "Seña" : "Pago"}
                      {payment.method ? ` · ${payment.method}` : ""}
                    </span>
                    <span className="text-slate-800">{formatCurrency(payment.amount)}</span>
                  </li>
                ))}
              </ul>
            )}

            <form onSubmit={handleAddPayment} className="mt-4 flex flex-wrap items-end gap-3 border-t border-slate-100 pt-4">
              <Input
                label="Monto"
                type="number"
                min={0}
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
              />
              <Select
                label="Tipo"
                value={paymentType}
                onChange={(event) => setPaymentType(event.target.value as PaymentType)}
              >
                <option value="pago">Pago</option>
                <option value="adelanto">Seña</option>
              </Select>
              <Input label="Medio" value={method} onChange={(event) => setMethod(event.target.value)} />
              <Button type="submit" isLoading={addPayment.isPending}>
                Registrar pago
              </Button>
            </form>
            {addPayment.error instanceof ApiError && (
              <p className="mt-2 text-sm text-red-600">{addPayment.error.message}</p>
            )}
          </section>
        </div>

        <aside className="flex flex-col gap-4">
          <section className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-semibold text-slate-800">Estado</h2>
            <div className="mb-3 flex items-center gap-2">
              <StatusBadge status={sale.status} />
              <PaymentBadge sale={sale} />
            </div>
            <Select
              label="Cambiar estado"
              value={sale.status}
              onChange={(event) => updateSale.mutate({ status: event.target.value as SaleStatus })}
            >
              <option value="pendiente">Pendiente</option>
              <option value="en_proceso">En proceso</option>
              <option value="entregado">Entregado</option>
              <option value="cancelado">Cancelado</option>
            </Select>
            {sale.ship_by && (
              <p className="mt-3 text-xs text-slate-500">Enviar antes de {formatDate(sale.ship_by)}</p>
            )}
            {sale.payment_due && (
              <p className="mt-1 text-xs text-slate-500">Cobrar antes de {formatDate(sale.payment_due)}</p>
            )}
          </section>

          {sale.notes && (
            <section className="rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="mb-2 text-sm font-semibold text-slate-800">Notas</h2>
              <p className="text-sm text-slate-600">{sale.notes}</p>
            </section>
          )}

          <section className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-semibold text-slate-800">Acciones</h2>
            <Button
              variant="danger"
              disabled={sale.payments.length > 0}
              onClick={() => setConfirmingDelete(true)}
            >
              Eliminar orden
            </Button>
            {sale.payments.length > 0 && (
              <p className="mt-2 text-xs text-slate-500">
                No se puede eliminar una orden con pagos registrados.
              </p>
            )}
          </section>
        </aside>
      </div>

      <ConfirmDialog
        open={isConfirmingDelete}
        title="Eliminar orden"
        description="Esta acción no se puede deshacer."
        isLoading={deleteSale.isPending}
        error={deleteSale.error instanceof ApiError ? deleteSale.error.message : null}
        onConfirm={handleDelete}
        onCancel={() => setConfirmingDelete(false)}
      />
    </div>
  );
}

function Row({ label, value, strong = false }: { label: string; value: string; strong?: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-slate-500">{label}</dt>
      <dd className={strong ? "font-semibold text-slate-900" : "text-slate-700"}>{value}</dd>
    </div>
  );
}