import type { Sale, SaleStatus } from "@/types/domain";

const statusLabels: Record<SaleStatus, string> = {
  pendiente: "Pendiente",
  en_proceso: "En proceso",
  entregado: "Entregado",
  cancelado: "Cancelado",
};

const statusColors: Record<SaleStatus, string> = {
  pendiente: "bg-slate-100 text-slate-600",
  en_proceso: "bg-amber-50 text-amber-600",
  entregado: "bg-emerald-50 text-emerald-600",
  cancelado: "bg-slate-200 text-slate-500",
};

export function StatusBadge({ status }: { status: SaleStatus }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[status]}`}>
      {statusLabels[status]}
    </span>
  );
}

const paymentLabels = {
  sin_pago: "Sin pago",
  parcial: "Parcial",
  pagada: "Pagada",
} as const;

export function paymentStatus(sale: Sale): keyof typeof paymentLabels {
  if (sale.balance <= 0) return "pagada";
  if (sale.paid <= 0) return "sin_pago";
  return "parcial";
}

export function PaymentBadge({ sale }: { sale: Sale }) {
  const status = paymentStatus(sale);
  const colors: Record<keyof typeof paymentLabels, string> = {
    sin_pago: "bg-red-50 text-red-600",
    parcial: "bg-amber-50 text-amber-600",
    pagada: "bg-emerald-50 text-emerald-600",
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${colors[status]}`}>
      {paymentLabels[status]}
    </span>
  );
}