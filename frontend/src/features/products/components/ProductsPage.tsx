import { useMemo, useState } from "react";

import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { DataTable, type Column } from "@/components/common/DataTable";
import { ExportButtons } from "@/components/common/ExportButtons";
import { PageHeader } from "@/components/common/PageHeader";
import { SearchInput } from "@/components/common/SearchInput";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { useProviders } from "@/features/providers/hooks";
import { useUrlFilters } from "@/hooks/useUrlFilters";
import { ApiError } from "@/lib/http";
import { formatCurrency } from "@/lib/format";
import type { Product } from "@/types/domain";

import { useCreateProduct, useDeleteProduct, useProducts, useUpdateProduct, useAdjustStock } from "../hooks";
import type { ProductFormOutput } from "../types";
import { ProductForm } from "./ProductForm";
import { StockAdjustForm } from "./StockAdjustForm";
import { StockMovesList } from "./StockMovesList";

export function ProductsPage() {
  const { get, setParam } = useUrlFilters();
  const search = get("search");
  const category = get("category");
  const providerId = get("provider");
  const activeOnly = get("active") !== "0";

  const [editing, setEditing] = useState<Product | null>(null);
  const [isFormOpen, setFormOpen] = useState(false);
  const [adjusting, setAdjusting] = useState<Product | null>(null);
  const [moving, setMoving] = useState<Product | null>(null);
  const [deleting, setDeleting] = useState<Product | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data, isLoading, error, refetch } = useProducts({
    search,
    category,
    provider_id: providerId,
    active_only: activeOnly,
  });
  const { data: providers } = useProviders({});
  const createProduct = useCreateProduct();
  const updateProduct = useUpdateProduct();
  const stockAdjust = useAdjustStock();
  const deleteProduct = useDeleteProduct();

  const providerNames = useMemo(() => {
    const map = new Map<string, string>();
    for (const provider of providers ?? []) map.set(provider.id, provider.name);
    return map;
  }, [providers]);

  const formError =
    (createProduct.error instanceof ApiError && createProduct.error.message) ||
    (updateProduct.error instanceof ApiError && updateProduct.error.message) ||
    null;

  function openCreate() {
    createProduct.reset();
    updateProduct.reset();
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(product: Product) {
    createProduct.reset();
    updateProduct.reset();
    setEditing(product);
    setFormOpen(true);
  }

  function handleSubmit(input: ProductFormOutput) {
    if (editing) {
      updateProduct.mutate({ id: editing.id, input }, { onSuccess: () => setFormOpen(false) });
    } else {
      createProduct.mutate(input, { onSuccess: () => setFormOpen(false) });
    }
  }

  function handleAdjust(quantity: number, reason: string) {
    if (!adjusting) return;
    stockAdjust.mutate(
      { product_id: adjusting.id, quantity, reason },
      { onSuccess: () => setAdjusting(null) },
    );
  }

  function confirmDelete() {
    if (!deleting) return;
    setDeleteError(null);
    deleteProduct.mutate(deleting.id, {
      onSuccess: () => setDeleting(null),
      onError: (err) =>
        setDeleteError(err instanceof ApiError ? err.message : "No pudimos eliminar el producto."),
    });
  }

  const columns: Column<Product>[] = [
    { key: "name", header: "Nombre" },
    { key: "category", header: "Categoría", render: (row) => row.category ?? "—" },
    {
      key: "provider",
      header: "Proveedor",
      render: (row) => providerNames.get(row.provider_id) ?? "—",
    },
    {
      key: "price",
      header: "Precio",
      render: (row) => (row.price != null ? formatCurrency(row.price) : "—"),
    },
    {
      key: "stock",
      header: "Stock",
      render: (row) => {
        if (row.stock === 0) return <span className="font-medium text-red-600">Agotado</span>;
        if (row.stock <= row.min_stock) return <span className="text-amber-600">{row.stock}</span>;
        return <span>{row.stock}</span>;
      },
    },
    {
      key: "actions",
      header: "",
      className: "text-right",
      render: (row) => (
        <div className="flex justify-end gap-3">
          <button
            type="button"
            className="text-sm font-medium text-brand-600 hover:underline"
            onClick={() => openEdit(row)}
          >
            Editar
          </button>
          <button
            type="button"
            className="text-sm font-medium text-slate-600 hover:underline"
            onClick={() => {
              stockAdjust.reset();
              setAdjusting(row);
            }}
          >
            Ajustar stock
          </button>
          <button
            type="button"
            className="text-sm font-medium text-slate-600 hover:underline"
            onClick={() => setMoving(row)}
          >
            Movimientos
          </button>
          <button
            type="button"
            className="text-sm font-medium text-red-600 hover:underline"
            onClick={() => {
              setDeleteError(null);
              setDeleting(row);
            }}
          >
            Eliminar
          </button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Productos"
        description="Catálogo, precios y control de stock."
        actions={<Button onClick={openCreate}>Nuevo producto</Button>}
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <SearchInput
          value={search}
          onChange={(value) => setParam("search", value)}
          placeholder="Buscar producto…"
        />
        <input
          type="text"
          value={category}
          placeholder="Categoría"
          onChange={(event) => setParam("category", event.target.value)}
          className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-900 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
        />
        <select
          value={providerId}
          onChange={(event) => setParam("provider", event.target.value)}
          className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-700 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
        >
          <option value="">Todos los proveedores</option>
          {(providers ?? []).map((provider) => (
            <option key={provider.id} value={provider.id}>
              {provider.name}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={activeOnly}
            onChange={(event) => setParam("active", event.target.checked ? "" : "0")}
          />
          Sólo activos
        </label>
        <ExportButtons
          entity="products"
          disabled={(data ?? []).length === 0}
          params={{
            search: search || undefined,
            category: category || undefined,
            provider_id: providerId || undefined,
            active_only: activeOnly,
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
        emptyTitle="No hay productos"
        emptyDescription="Creá el primer producto para empezar a vender."
        emptyAction={<Button onClick={openCreate}>Nuevo producto</Button>}
      />

      <Modal
        open={isFormOpen}
        title={editing ? "Editar producto" : "Nuevo producto"}
        onClose={() => setFormOpen(false)}
      >
        <ProductForm
          product={editing}
          providers={providers ?? []}
          isSubmitting={createProduct.isPending || updateProduct.isPending}
          error={formError}
          onSubmit={handleSubmit}
          onCancel={() => setFormOpen(false)}
        />
      </Modal>

      <Modal open={Boolean(adjusting)} title="Ajustar stock" onClose={() => setAdjusting(null)}>
        {adjusting && (
          <StockAdjustForm
            product={adjusting}
            isSubmitting={stockAdjust.isPending}
            error={stockAdjust.error instanceof ApiError ? stockAdjust.error.message : null}
            onSubmit={handleAdjust}
            onCancel={() => setAdjusting(null)}
          />
        )}
      </Modal>

      <Modal open={Boolean(moving)} title="Historial de movimientos" onClose={() => setMoving(null)}>
        {moving && <StockMovesList product={moving} />}
      </Modal>

      <ConfirmDialog
        open={Boolean(deleting)}
        title="Eliminar producto"
        description={`¿Querés eliminar "${deleting?.name ?? ""}"?`}
        isLoading={deleteProduct.isPending}
        error={deleteError}
        onConfirm={confirmDelete}
        onCancel={() => setDeleting(null)}
      />
    </div>
  );
}