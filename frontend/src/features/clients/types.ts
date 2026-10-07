import type { ClientType } from "@/types/domain";

export interface ClientInput {
  name: string;
  phone?: string;
  email?: string;
  instagram?: string;
  address?: string;
  type?: ClientType;
  notes?: string;
}

export type ClientUpdateInput = Partial<ClientInput>;

export interface ClientFilters {
  search?: string;
  client_type?: string;
}