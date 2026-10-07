import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/common/PageHeader";
import { Select } from "@/components/ui/Select";
import { Textarea } from "@/components/ui/Textarea";
import { useClients } from "@/features/clients/hooks";
import { useProducts } from "@/features/products/hooks";
import { ApiError } from "@/lib/http";
import { formatCurrency, formatDateInput } from "@/lib/format";
import type { SaleClientType } from "@/types/domain";

import { useCreateSale } from "../hooks";

interface DraftItem {
  key: string;
  productId: string;
  description: string;
  qty: string;
  unitPrice: string;
}

function newDraftItem(): DraftItem {
  return { key: crypto.randomUUID(), productId: "", description: "", qty: "1", unitPrice: "" };
}

export function OrderCreatePage() {
  const navigate = useNavigate();
  const { data: clients } = useClients();
  const { data: products } = useProducts({ active_only: true });
  const createSale = useCreateSale();

  const [clientId, setClientId] = useState("");
  const [clientType, setClientType] = useState<SaleClientType>("minorista");
  const [date, setDate] = useState(formatDateInput(new Date()));
  const [items, setItems] = useState<DraftItem[]>([newDraftItem()]);
  const [discountMode, setDiscountMode] = useState<"amount" | "pct">("amount");
  const [discountValue, setDiscountValue] = useState("");
  const [shipping, setShipping] = useState("");
  const [notes, setNotes] = useState("");
  const [shipBy, setShipBy] = useState("");
  const [paymentDue, setPaymentDue] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const productMap = useMemo(() => {
    const map = new Map((products ?? []).map((product) => [product.id, product]));
    return map;
  }, [products]);

  function priceFor(productId: string): number | null {
    const product = productMap.get(productId);
    if (!product) return null;
    const value = clientType === "mayorista" ? product.price_mayorista : product.price;
    return value ?? product.price ?? null;
  }

  function updateItem(key: string, patch: Partial<DraftItem>) {
    setItems((prev) => prev.map((item) => (item.key === key ? { ...item, ...patch } : item)));
  }

  const subtotal = items.reduce((sum, item) => {
    const qty = Number(item.qty) || 0;
    if (item.productId) return sum + qty * (priceFor(item.productId) ?? 0);
    return sum + qty * (Number(item.unitPrice) || 0);
  }, 0);

  const discountValueNumber = Number(discountValue) || 0;
  const discountAmount =
    discountMode === "pct" ? Math.round((subtotal * discountValueNumber) / 100) : discountValueNumber;
  const total = subtotal - discountAmount + (Number(shipping) || 0);

  function handleClientChange(id: string) {
    setClientId(id);
    const client = clients?.find((entry) => entry.id === id);
    if (client && client.type !== "ambos") setClientType(client.type);
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);

    if (!clientId) {
      setFormError("Seleccioná un cliente.");
      return;
    }

    const payloadItems = [];
    for (const item of items) {
      const qty = Number(item.qty);
      if (!qty || qty <= 0) continue;
      if (item.productId) {
        payloadItems.push({ product_id: item.productId, qty });
      } else if (item.description.trim() && item.unitPrice) {
        payloadItems.push({
          description: item.description.trim(),
          qty,
          unit_price: Number(item.unitPrice),
        });
      }
    }

    if (payloadItems.length === 0) {
      setFormError("Agregá al menos un ítem con producto o descripción y precio.");
      return;
    }

    createSale.mutate(
      {
        client_id: clientId,
        client_type: clientType,
        date: date || undefined,
        items: payloadItems,
        shipping_cost: Number(shipping) || 0,
        discount: discountMode === "amount" ? discountValueNumber : undefined,
        discount_pct: discountMode === "pct" ? discountValueNumber : undefined,
        notes: notes.trim() || undefined,
        ship_by: shipBy || undefined,
        payment_due: paymentDue || undefined,
      },
      {
        onSuccess: (sale) => navigate(`/ordenes/${sale.id}`),
        onError: (error) =>
          setFormError(error instanceof ApiError ? error.message : "No pudimos crear la orden."),
      },
    );
  }

  return (
    <div>
      <PageHeader
        title="Nueva orden"
        description="Cargá los ítems de catálogo, libres, o una combinación de ambos."
        actions={
          <Link to="/ordenes">
            <Button variant="secondary">Volver</Button>
          </Link>
        }
      />

      <form onSubmit={handleSubmit} className="flex flex-col gap-6" noValidate>
        <div className="grid grid-cols-1 gap-4 rounded-xl border border-slate-200 bg-white p-5 sm:grid-cols-2">
          <Select label="Cliente" name="client" value={clientId} onChange={(event) => handleClientChange(event.target.value)}>
            <option value="">Seleccioná un cliente…</option>
            {(clients ?? []).map((client) => (
              <option key={client.id} value={client.id}>
                {client.name}
              </option>
            ))}
          </Select>
          <Select
            label="Lista de precios"
            name="client_type"
            value={clientType}
            onChange={(event) => setClientType(event.target.value as SaleClientType)}
          >
            <option value="minorista">Minorista</option>
            <option value="mayorista">Mayorista</option>
          </Select>
          <Input label="Fecha" name="date" type="date" value={date} onChange={(event) => setDate(event.target.value)} />
          <Input
            label="Enviar antes de"
            name="ship_by"
            type="date"
            value={shipBy}
            onChange={(event) => setShipBy(event.target.value)}
          />
        </div>

        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-800">Ítems</h2>
            <Button type="button" variant="secondary" size="sm" onClick={() => setItems((prev) => [...prev, newDraftItem()])}>
              Agregar ítem
            </Button>
          </div>
          <div className="flex flex-col gap-3">
            {items.map((item) => (
              <div key={item.key} className="grid grid-cols-1 gap-2 sm:grid-cols-[2fr_4rem_6rem_auto] sm:items-end">
                <div className="flex flex-col gap-2">
                  <select
                    value={item.productId}
                    onChange={(event) => updateItem(item.key, { productId: event.target.value })}
                    className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-700 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
                  >
                    <option value="">Ítem libre…</option>
                    {(products ?? []).map((product) => (
                      <option key={product.id} value={product.id}>
                        {product.name}
                      </option>
                    ))}
                  </select>
                  {!item.productId && (
                    <input
                      type="text"
                      value={item.description}
                      placeholder="Descripción del ítem libre"
                      onChange={(event) => updateItem(item.key, { description: event.target.value })}
                      className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-900 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
                    />
                  )}
                </div>
                <Input
                  label="Cant."
                  type="number"
                  min={1}
                  value={item.qty}
                  onChange={(event) => updateItem(item.key, { qty: event.target.value })}
                />
                <Input
                  label="Precio"
                  type="number"
                  min={0}
                  value={item.productId ? String(priceFor(item.productId) ?? "") : item.unitPrice}
                  disabled={Boolean(item.productId)}
                  onChange={(event) => updateItem(item.key, { unitPrice: event.target.value })}
                />
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setItems((prev) => prev.filter((entry) => entry.key !== item.key))}
                  disabled={items.length === 1}
                >
                  Quitar
                </Button>
              </div>
            ))}
          </div>
        </section>

        <section className="grid grid-cols-1 gap-4 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-2">
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-2">
              <Select
                label="Descuento"
                value={discountMode}
                onChange={(event) => setDiscountMode(event.target.value as "amount" | "pct")}
              >
                <option value="amount">Monto ($)</option>
                <option value="pct">Porcentaje (%)</option>
              </Select>
              <Input
                label="Valor"
                type="number"
                min={0}
                value={discountValue}
                onChange={(event) => setDiscountValue(event.target.value)}
              />
            </div>
            <Input label="Envío" type="number" min={0} value={shipping} onChange={(event) => setShipping(event.target.value)} />
            <Input
              label="Vencimiento de cobro"
              type="date"
              value={paymentDue}
              onChange={(event) => setPaymentDue(event.target.value)}
            />
          </div>
          <Textarea label="Notas" value={notes} onChange={(event) => setNotes(event.target.value)} />
        </section>

        <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4">
          <dl className="flex gap-6 text-sm">
            <div>
              <dt className="text-slate-500">Subtotal</dt>
              <dd className="font-medium text-slate-800">{formatCurrency(subtotal)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Descuento</dt>
              <dd className="font-medium text-slate-800">-{formatCurrency(discountAmount)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Total</dt>
              <dd className="text-lg font-semibold text-slate-900">{formatCurrency(total)}</dd>
            </div>
          </dl>
          <div className="flex items-center gap-2">
            <Link to="/ordenes">
              <Button type="button" variant="secondary">
                Cancelar
              </Button>
            </Link>
            <Button type="submit" isLoading={createSale.isPending}>
              Crear orden
            </Button>
          </div>
        </div>

        {createSale.error instanceof ApiError && (
          <p role="alert" className="text-sm text-red-600">
            {createSale.error.message}
          </p>
        )}
        {formError && (
          <p role="alert" className="text-sm text-red-600">
            {formError}
          </p>
        )}
      </form>
    </div>
  );
}