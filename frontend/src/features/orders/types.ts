import type { SaleStatus, SaleClientType, PaymentType } from "@/types/domain";

export interface SaleFilters {
  status?: string;
  client_id?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface SaleItemInput {
  product_id?: string;
  description?: string;
  qty: number;
  unit_price?: number;
}

export interface SaleInput {
  client_id: string;
  client_type?: SaleClientType;
  date?: string;
  items: SaleItemInput[];
  shipping_cost?: number;
  discount?: number;
  discount_pct?: number;
  notes?: string;
  ship_by?: string;
  payment_due?: string;
}

export interface SaleUpdateInput {
  status?: SaleStatus;
  shipping_cost?: number;
  discount?: number;
  discount_pct?: number;
  notes?: string;
  ship_by?: string;
  payment_due?: string;
}

export interface PaymentInput {
  amount: number;
  date?: string;
  type?: PaymentType;
  method?: string;
  notes?: string;
}