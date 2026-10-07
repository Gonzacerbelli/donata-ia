export interface ProductFilters {
  search?: string;
  category?: string;
  provider_id?: string;
  active_only?: boolean;
}

export interface ProductInput {
  name: string;
  category?: string;
  description?: string;
  price?: number;
  price_mayorista?: number;
  cost?: number;
  stock?: number;
  min_stock?: number;
  unit?: string;
  provider_id: string;
}

export type ProductUpdateInput = Partial<ProductInput> & { active?: boolean };

export type ProductFormOutput = ProductInput & { active?: boolean };

export interface StockAdjustInput {
  product_id: string;
  quantity: number;
  reason: string;
}