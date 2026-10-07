import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import type { Provider } from "@/types/domain";

import type { ProviderInput } from "../types";

interface ProviderFormProps {
  provider?: Provider | null;
  isSubmitting: boolean;
  error?: string | null;
  onSubmit: (input: ProviderInput) => void;
  onCancel: () => void;
}

function opt(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
}

export function ProviderForm({ provider, isSubmitting, error, onSubmit, onCancel }: ProviderFormProps) {
  const [name, setName] = useState(provider?.name ?? "");
  const [contact, setContact] = useState(provider?.contact ?? "");
  const [phone, setPhone] = useState(provider?.phone ?? "");
  const [email, setEmail] = useState(provider?.email ?? "");
  const [cuit, setCuit] = useState(provider?.cuit ?? "");
  const [notes, setNotes] = useState(provider?.notes ?? "");
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
      contact: opt(contact),
      phone: opt(phone),
      email: opt(email),
      cuit: opt(cuit),
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
      <Input
        label="Contacto"
        name="contact"
        value={contact}
        onChange={(event) => setContact(event.target.value)}
      />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label="Teléfono"
          name="phone"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
        />
        <Input
          label="CUIT"
          name="cuit"
          value={cuit}
          onChange={(event) => setCuit(event.target.value)}
        />
      </div>
      <Input
        label="Email"
        name="email"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />
      <Textarea
        label="Notas"
        name="notes"
        value={notes}
        onChange={(event) => setNotes(event.target.value)}
      />
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