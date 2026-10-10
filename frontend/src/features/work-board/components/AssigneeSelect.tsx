import { Select } from "@/components/ui/Select";

import { useUsers } from "../hooks";

interface AssigneeSelectProps {
  value: string | null;
  disabled?: boolean;
  onChange: (value: string | null) => void;
}

export function AssigneeSelect({ value, disabled, onChange }: AssigneeSelectProps) {
  const { data: users } = useUsers();
  return (
    <Select
      aria-label="Usuario asignado"
      value={value ?? ""}
      disabled={disabled}
      className="w-full"
      onChange={(event) => onChange(event.target.value || null)}
    >
      <option value="">Sin asignar</option>
      {(users ?? []).map((user) => (
        <option key={user.id} value={user.id}>
          {user.name ?? user.email ?? "Usuario"}
        </option>
      ))}
    </Select>
  );
}
