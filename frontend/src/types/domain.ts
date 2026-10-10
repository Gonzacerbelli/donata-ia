export type ClientType = "minorista" | "mayorista" | "ambos";
export type SaleClientType = "minorista" | "mayorista";
export type SaleStatus = "pendiente" | "en_proceso" | "entregado" | "cancelado";
export type PaymentType = "adelanto" | "pago";
export type StockMoveRefType = "venta" | "cancelacion" | "compra" | "ajuste";

export interface Provider {
  id: string;
  name: string;
  contact: string | null;
  phone: string | null;
  email: string | null;
  cuit: string | null;
  notes: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: string;
  name: string;
  category: string | null;
  description: string | null;
  price: number | null;
  price_mayorista: number | null;
  cost: number | null;
  stock: number;
  min_stock: number;
  unit: string;
  provider_id: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Client {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  instagram: string | null;
  address: string | null;
  type: ClientType;
  notes: string | null;
  created_at: string;
}

export interface SaleItem {
  product_id: string | null;
  description: string | null;
  qty: number;
  unit_price: number | null;
}

export interface Payment {
  amount: number;
  date: string;
  type: PaymentType;
  method: string | null;
  notes: string | null;
}

export interface Sale {
  id: string;
  client_id: string;
  client_type: SaleClientType;
  date: string;
  items: SaleItem[];
  subtotal: number;
  shipping_cost: number;
  discount: number;
  discount_pct: number | null;
  total: number;
  status: SaleStatus;
  payments: Payment[];
  notes: string | null;
  ship_by: string | null;
  payment_due: string | null;
  created_at: string;
  updated_at: string;
  paid: number;
  balance: number;
}

export interface StockMove {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  stock_after: number;
  reason: string | null;
  ref_type: StockMoveRefType | null;
  ref_id: string | null;
  created_at: string;
}

export interface SalesSummary {
  sales_count: number;
  revenue: number;
  collected: number;
  receivable: number;
  average_ticket: number;
}

export interface TopProduct {
  description: string;
  qty: number;
  revenue: number;
}

export interface InventoryValue {
  inventory_value: number;
  units: number;
}

export type WorkStatus = "pendiente" | "en_curso" | "bloqueado" | "terminado";
export type WorkPriority = "alta" | "media" | "baja";

export interface WorkComment {
  id: string;
  author_id: string;
  author_name: string;
  text: string;
  created_at: string;
}

export interface WorkCard {
  sale_id: string;
  client_id: string;
  date: string;
  items: SaleItem[];
  total: number;
  status: WorkStatus;
  priority: WorkPriority;
  assigned_to: string | null;
  comments: WorkComment[];
}

export interface UserSummary {
  id: string;
  name: string | null;
  email: string | null;
}

export type NotificationSeverity = "alta" | "media" | "baja";
export type NotificationEntity = "product" | "sale";

export interface AppNotification {
  id: string;
  type: string;
  severity: NotificationSeverity;
  title: string;
  description: string;
  entity: NotificationEntity;
  entity_id: string;
  action: string | null;
  read: boolean;
  dismissed: boolean;
  created_at: string | null;
}

export interface NotificationList {
  items: AppNotification[];
  unread_count: number;
}

export interface ChatThread {
  id: string;
  thread_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  thread_id: string;
  role: "user" | "assistant";
  content: string;
  tool_calls: Record<string, unknown>[];
  created_at: string;
}

export interface PendingAction {
  token: string;
  tool: string;
  args: Record<string, unknown>;
  summary: string;
}

export interface ChatResponse {
  thread_id: string;
  tool_calls: Record<string, unknown>[];
  response: string;
  pending_action: PendingAction | null;
}

export interface ChatStreamToken {
  delta: string;
}

export interface ChatStreamToolStart {
  name: string;
  arguments: Record<string, unknown>;
}

export interface ChatStreamToolEnd {
  name: string;
  ok: boolean;
  result: unknown;
}

export interface ChatStreamError {
  detail: string;
}

export type ChatStreamEvent =
  | { event: "start"; data: { thread_id: string } }
  | { event: "token"; data: ChatStreamToken }
  | { event: "tool_start"; data: ChatStreamToolStart }
  | { event: "tool_end"; data: ChatStreamToolEnd }
  | { event: "pending_action"; data: PendingAction }
  | { event: "done"; data: ChatResponse }
  | { event: "error"; data: ChatStreamError };