import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Textarea } from "@/components/ui/Textarea";
import type { Client, ClientType } from "@/types/domain";

import type { ClientInput } from "../types";

interface ClientFormProps {
  client?: Client | null;
  isSubmitting: boolean;
  error?: string | null;
  onSubmit: (input: ClientInput) => void;
  onCancel: () => void;
}

function opt(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
}

export function ClientForm({ client, isSubmitting, error, onSubmit, onCancel }: ClientFormProps) {
  const [name, setName] = useState(client?.name ?? "");
  const [phone, setPhone] = useState(client?.phone ?? "");
  const [email, setEmail] = useState(client?.email ?? "");
  const [instagram, setInstagram] = useState(client?.instagram ?? "");
  const [address, setAddress] = useState(client?.address ?? "");
  const [type, setType] = useState<ClientType>(client?.type ?? "minorista");
  const [notes, setNotes] = useState(client?.notes ?? "");
  const [nameError, setNameError] = useState<string | null>(null);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim()) {
      setNameError("Ingresá un nombre");
      return;
    }
    setNameError(null);
    onSubmit({
      name: name.trim(),
      phone: opt(phone),
      email: opt(email),
      instagram: opt(instagram),
      address: opt(address),
      type,
      notes: opt(notes),
    });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <Input
        label="Nombre"
        name="name"
        value={name}
        error={nameError ?? undefined}
        onChange={(event) => setName(event.target.value)}
      />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input label="Teléfono" name="phone" value={phone} onChange={(event) => setPhone(event.target.value)} />
        <Input label="Email" name="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input label="Instagram" name="instagram" value={instagram} onChange={(event) => setInstagram(event.target.value)} />
        <Select label="Tipo" name="type" value={type} onChange={(event) => setType(event.target.value as ClientType)}>
          <option value="minorista">Minorista</option>
          <option value="mayorista">Mayorista</option>
          <option value="ambos">Ambos</option>
        </Select>
      </div>
      <Input label="Dirección" name="address" value={address} onChange={(event) => setAddress(event.target.value)} />
      <Textarea label="Notas" name="notes" value={notes} onChange={(event) => setNotes(event.target.value)} />
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