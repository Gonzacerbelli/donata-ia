export interface ProviderInput {
  name: string;
  contact?: string;
  phone?: string;
  email?: string;
  cuit?: string;
  notes?: string;
}

export interface ProviderUpdateInput extends Partial<ProviderInput> {
  active?: boolean;
}

export interface ProviderFilters {
  search?: string;
  active_only?: boolean;
}