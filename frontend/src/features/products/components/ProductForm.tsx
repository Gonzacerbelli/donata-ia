import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Textarea } from "@/components/ui/Textarea";
import type { Product, Provider } from "@/types/domain";

import type { ProductFormOutput } from "../types";

interface ProductFormProps {
  product?: Product | null;
  providers: Provider[];
  isSubmitting: boolean;
  error?: string | null;
  onSubmit: (input: ProductFormOutput) => void;
  onCancel: () => void;
}

function toInt(value: string): number | undefined {
  if (!value.trim()) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.round(parsed) : undefined;
}

function opt(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
}

export function ProductForm({
  product,
  providers,
  isSubmitting,
  error,
  onSubmit,
  onCancel,
}: ProductFormProps) {
  const isEdit = Boolean(product);
  const [name, setName] = useState(product?.name ?? "");
  const [providerId, setProviderId] = useState(product?.provider_id ?? "");
  const [category, setCategory] = useState(product?.category ?? "");
  const [unit, setUnit] = useState(product?.unit ?? "unidad");
  const [price, setPrice] = useState(product?.price != null ? String(product.price) : "");
  const [priceMayorista, setPriceMayorista] = useState(
    product?.price_mayorista != null ? String(product.price_mayorista) : "",
  );
  const [cost, setCost] = useState(product?.cost != null ? String(product.cost) : "");
  const [minStock, setMinStock] = useState(String(product?.min_stock ?? 0));
  const [stock, setStock] = useState(String(product?.stock ?? 0));
  const [description, setDescription] = useState(product?.description ?? "");
  const [active, setActive] = useState(product?.active ?? true);
  const [errors, setErrors] = useState<{ name?: string; provider?: string }>({});

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const nextErrors: { name?: string; provider?: string } = {};
    if (!name.trim()) nextErrors.name = "Ingresá un nombre";
    if (!providerId) nextErrors.provider = "Seleccioná un proveedor";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    const base = {
      name: name.trim(),
      provider_id: providerId,
      category: opt(category),
      unit: opt(unit),
      price: toInt(price),
      price_mayorista: toInt(priceMayorista),
      cost: toInt(cost),
      min_stock: toInt(minStock),
      description: opt(description),
    };

    if (isEdit) {
      onSubmit({ ...base, active });
    } else {
      onSubmit({ ...base, stock: toInt(stock) ?? 0 });
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <Input
        label="Nombre"
        name="name"
        value={name}
        error={errors.name}
        onChange={(event) => setName(event.target.value)}
      />
      <Select
        label="Proveedor"
        name="provider_id"
        value={providerId}
        error={errors.provider}
        onChange={(event) => setProviderId(event.target.value)}
      >
        <option value="">Seleccioná un proveedor…</option>
        {providers.map((provider) => (
          <option key={provider.id} value={provider.id}>
            {provider.name}
          </option>
        ))}
      </Select>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label="Categoría"
          name="category"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
        />
        <Input label="Unidad" name="unit" value={unit} onChange={(event) => setUnit(event.target.value)} />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Input
          label="Precio minorista"
          name="price"
          type="number"
          min={0}
          value={price}
          onChange={(event) => setPrice(event.target.value)}
        />
        <Input
          label="Precio mayorista"
          name="price_mayorista"
          type="number"
          min={0}
          value={priceMayorista}
          onChange={(event) => setPriceMayorista(event.target.value)}
        />
        <Input
          label="Costo"
          name="cost"
          type="number"
          min={0}
          value={cost}
          onChange={(event) => setCost(event.target.value)}
        />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label="Stock mínimo"
          name="min_stock"
          type="number"
          min={0}
          value={minStock}
          onChange={(event) => setMinStock(event.target.value)}
        />
        {!isEdit && (
          <Input
            label="Stock inicial"
            name="stock"
            type="number"
            min={0}
            value={stock}
            onChange={(event) => setStock(event.target.value)}
          />
        )}
      </div>
      <Textarea
        label="Descripción"
        name="description"
        value={description}
        onChange={(event) => setDescription(event.target.value)}
      />
      {isEdit && (
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input type="checkbox" checked={active} onChange={(event) => setActive(event.target.checked)} />
          Producto activo
        </label>
      )}
      {isEdit && (
        <p className="text-xs text-slate-500">
          El stock se modifica desde “Ajustar stock”, no desde esta ficha.
        </p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isSubmitting}>
          Cancelar
        </Button>
        <Button type="submit" isLoading={isSubmitting}>
          Guardar
        </Button>
      </div>
    </form>
  );
}