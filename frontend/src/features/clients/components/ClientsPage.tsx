import { useState } from "react";

import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { DataTable, type Column } from "@/components/common/DataTable";
import { ExportButtons } from "@/components/common/ExportButtons";
import { PageHeader } from "@/components/common/PageHeader";
import { SearchInput } from "@/components/common/SearchInput";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { useUrlFilters } from "@/hooks/useUrlFilters";
import { ApiError } from "@/lib/http";
import type { Client } from "@/types/domain";

import { useCreateClient, useDeleteClient, useClients, useUpdateClient } from "../hooks";
import type { ClientInput } from "../types";
import { ClientForm } from "./ClientForm";
import { ClientSummary } from "./ClientSummary";

const typeLabels: Record<string, string> = {
  minorista: "Minorista",
  mayorista: "Mayorista",
  ambos: "Ambos",
};

export function ClientsPage() {
  const { get, setParam } = useUrlFilters();
  const search = get("search");
  const clientType = get("type");

  const [editing, setEditing] = useState<Client | null>(null);
  const [isFormOpen, setFormOpen] = useState(false);
  const [viewing, setViewing] = useState<Client | null>(null);
  const [deleting, setDeleting] = useState<Client | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data, isLoading, error, refetch } = useClients({ search, client_type: clientType });
  const createClient = useCreateClient();
  const updateClient = useUpdateClient();
  const deleteClient = useDeleteClient();

  const formError =
    (createClient.error instanceof ApiError && createClient.error.message) ||
    (updateClient.error instanceof ApiError && updateClient.error.message) ||
    null;

  function openCreate() {
    createClient.reset();
    updateClient.reset();
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(client: Client) {
    createClient.reset();
    updateClient.reset();
    setEditing(client);
    setFormOpen(true);
  }

  function handleSubmit(input: ClientInput) {
    if (editing) {
      updateClient.mutate({ id: editing.id, input }, { onSuccess: () => setFormOpen(false) });
    } else {
      createClient.mutate(input, { onSuccess: () => setFormOpen(false) });
    }
  }

  function confirmDelete() {
    if (!deleting) return;
    setDeleteError(null);
    deleteClient.mutate(deleting.id, {
      onSuccess: () => setDeleting(null),
      onError: (err) =>
        setDeleteError(err instanceof ApiError ? err.message : "No pudimos eliminar el cliente."),
    });
  }

  const columns: Column<Client>[] = [
    { key: "name", header: "Nombre" },
    { key: "phone", header: "Teléfono", render: (row) => row.phone ?? "—" },
    { key: "email", header: "Email", render: (row) => row.email ?? "—" },
    { key: "instagram", header: "Instagram", render: (row) => row.instagram ?? "—" },
    { key: "type", header: "Tipo", render: (row) => typeLabels[row.type] ?? row.type },
    {
      key: "actions",
      header: "",
      className: "text-right",
      render: (row) => (
        <div className="flex justify-end gap-3">
          <button
            type="button"
            className="text-sm font-medium text-slate-600 hover:underline"
            onClick={() => setViewing(row)}
          >
            Resumen
          </button>
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
        title="Clientes"
        description="Cartera de clientes y su historial."
        actions={<Button onClick={openCreate}>Nuevo cliente</Button>}
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <SearchInput
          value={search}
          onChange={(value) => setParam("search", value)}
          placeholder="Nombre, teléfono, email o Instagram…"
        />
        <select
          value={clientType}
          onChange={(event) => setParam("type", event.target.value)}
          className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-700 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
        >
          <option value="">Todos los tipos</option>
          <option value="minorista">Minorista</option>
          <option value="mayorista">Mayorista</option>
          <option value="ambos">Ambos</option>
        </select>
        <ExportButtons
          entity="clients"
          disabled={(data ?? []).length === 0}
          params={{ search: search || undefined, client_type: clientType || undefined }}
        />
      </div>

      <DataTable
        columns={columns}
        rows={data ?? []}
        getRowId={(row) => row.id}
        isLoading={isLoading}
        error={error}
        onRetry={() => refetch()}
        emptyTitle="No hay clientes"
        emptyDescription="Cargá tu primer cliente para poder generarle órdenes."
        emptyAction={<Button onClick={openCreate}>Nuevo cliente</Button>}
      />

      <Modal
        open={isFormOpen}
        title={editing ? "Editar cliente" : "Nuevo cliente"}
        onClose={() => setFormOpen(false)}
      >
        <ClientForm
          client={editing}
          isSubmitting={createClient.isPending || updateClient.isPending}
          error={formError}
          onSubmit={handleSubmit}
          onCancel={() => setFormOpen(false)}
        />
      </Modal>

      <Modal
        open={Boolean(viewing)}
        title={`Resumen de ${viewing?.name ?? ""}`}
        onClose={() => setViewing(null)}
      >
        {viewing && <ClientSummary client={viewing} />}
      </Modal>

      <ConfirmDialog
        open={Boolean(deleting)}
        title="Eliminar cliente"
        description={`¿Querés eliminar a ${deleting?.name ?? ""}? No se permite si tiene órdenes registradas.`}
        isLoading={deleteClient.isPending}
        error={deleteError}
        onConfirm={confirmDelete}
        onCancel={() => setDeleting(null)}
      />
    </div>
  );
}