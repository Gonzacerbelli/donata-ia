import { useState } from "react";

import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { DataTable, type Column } from "@/components/common/DataTable";
import { PageHeader } from "@/components/common/PageHeader";
import { SearchInput } from "@/components/common/SearchInput";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { useUrlFilters } from "@/hooks/useUrlFilters";
import { ApiError } from "@/lib/http";
import type { Provider } from "@/types/domain";

import { useCreateProvider, useDeleteProvider, useProviders, useUpdateProvider } from "../hooks";
import type { ProviderInput } from "../types";
import { ProviderForm } from "./ProviderForm";

export function ProvidersPage() {
  const { get, setParam } = useUrlFilters();
  const search = get("search");
  const activeOnly = get("active") === "1";

  const [editing, setEditing] = useState<Provider | null>(null);
  const [isFormOpen, setFormOpen] = useState(false);
  const [deleting, setDeleting] = useState<Provider | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data, isLoading, error, refetch } = useProviders({ search, active_only: activeOnly });
  const createProvider = useCreateProvider();
  const updateProvider = useUpdateProvider();
  const deleteProvider = useDeleteProvider();

  const submitError =
    (createProvider.error instanceof ApiError && createProvider.error.message) ||
    (updateProvider.error instanceof ApiError && updateProvider.error.message) ||
    null;

  function openCreate() {
    createProvider.reset();
    updateProvider.reset();
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(provider: Provider) {
    createProvider.reset();
    updateProvider.reset();
    setEditing(provider);
    setFormOpen(true);
  }

  function handleSubmit(input: ProviderInput) {
    if (editing) {
      updateProvider.mutate({ id: editing.id, input }, { onSuccess: () => setFormOpen(false) });
    } else {
      createProvider.mutate(input, { onSuccess: () => setFormOpen(false) });
    }
  }

  function confirmDelete() {
    if (!deleting) return;
    setDeleteError(null);
    deleteProvider.mutate(deleting.id, {
      onSuccess: () => setDeleting(null),
      onError: (err) =>
        setDeleteError(err instanceof ApiError ? err.message : "No pudimos eliminar el proveedor."),
    });
  }

  const columns: Column<Provider>[] = [
    { key: "name", header: "Nombre" },
    { key: "contact", header: "Contacto", render: (row) => row.contact ?? "—" },
    { key: "phone", header: "Teléfono", render: (row) => row.phone ?? "—" },
    { key: "email", header: "Email", render: (row) => row.email ?? "—" },
    {
      key: "active",
      header: "Estado",
      render: (row) => (
        <span className={row.active ? "text-emerald-600" : "text-slate-400"}>
          {row.active ? "Activo" : "Inactivo"}
        </span>
      ),
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
        title="Proveedores"
        description="Alta, edición y baja de proveedores."
        actions={<Button onClick={openCreate}>Nuevo proveedor</Button>}
      />

      <div className="mb-4 flex flex-wrap items-center gap-4">
        <SearchInput value={search} onChange={(value) => setParam("search", value)} placeholder="Buscar por nombre..." />
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={activeOnly}
            onChange={(event) => setParam("active", event.target.checked ? "1" : "")}
          />
          Sólo activos
        </label>
      </div>

      <DataTable
        columns={columns}
        rows={data ?? []}
        getRowId={(row) => row.id}
        isLoading={isLoading}
        error={error instanceof Error ? error : null}
        onRetry={() => void refetch()}
        emptyTitle="No hay proveedores"
        emptyDescription="Agregá tu primer proveedor para asociarlo a los productos."
        emptyAction={<Button size="sm" onClick={openCreate}>Nuevo proveedor</Button>}
      />

      <Modal
        open={isFormOpen}
        title={editing ? "Editar proveedor" : "Nuevo proveedor"}
        onClose={() => setFormOpen(false)}
      >
        <ProviderForm
          provider={editing}
          isSubmitting={createProvider.isPending || updateProvider.isPending}
          error={submitError || null}
          onSubmit={handleSubmit}
          onCancel={() => setFormOpen(false)}
        />
      </Modal>

      <ConfirmDialog
        open={Boolean(deleting)}
        title="Eliminar proveedor"
        description={`¿Querés eliminar a ${deleting?.name ?? ""}? Si tiene productos asociados no se podrá.`}
        isLoading={deleteProvider.isPending}
        error={deleteError}
        onConfirm={confirmDelete}
        onCancel={() => setDeleting(null)}
      />
    </div>
  );
}