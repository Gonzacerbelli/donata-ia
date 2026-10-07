import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import type { Product } from "@/types/domain";

interface StockAdjustFormProps {
  product: Product;
  isSubmitting: boolean;
  error?: string | null;
  onSubmit: (quantity: number, reason: string) => void;
  onCancel: () => void;
}

export function StockAdjustForm({ product, isSubmitting, error, onSubmit, onCancel }: StockAdjustFormProps) {
  const [quantity, setQuantity] = useState("");
  const [reason, setReason] = useState("");
  const [errors, setErrors] = useState<{ quantity?: string; reason?: string }>({});

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const parsed = Number(quantity);
    const nextErrors: { quantity?: string; reason?: string } = {};
    if (!quantity || !Number.isInteger(parsed) || parsed === 0) {
      nextErrors.quantity = "Ingresá un entero distinto de cero";
    }
    if (parsed < 0 && product.stock + parsed < 0) {
      nextErrors.quantity = "El ajuste no puede dejar el stock en negativo";
    }
    if (!reason.trim()) nextErrors.reason = "Indicá el motivo del ajuste";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;
    onSubmit(parsed, reason.trim());
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <p className="text-sm text-slate-600">
        Stock actual de <span className="font-medium text-slate-800">{product.name}</span>: {product.stock}
      </p>
      <Input
        label="Cantidad (positiva para ingresar, negativa para descontar)"
        name="quantity"
        type="number"
        value={quantity}
        error={errors.quantity}
        onChange={(event) => setQuantity(event.target.value)}
      />
      <Textarea
        label="Motivo"
        name="reason"
        value={reason}
        error={errors.reason}
        onChange={(event) => setReason(event.target.value)}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isSubmitting}>
          Cancelar
        </Button>
        <Button type="submit" isLoading={isSubmitting}>
          Ajustar
        </Button>
      </div>
    </form>
  );
}