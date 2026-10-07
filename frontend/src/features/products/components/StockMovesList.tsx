import { Spinner } from "@/components/ui/Spinner";
import { formatDateTime } from "@/lib/format";
import type { Product } from "@/types/domain";

import { useProductMoves } from "../hooks";

const refLabels: Record<string, string> = {
  venta: "Venta",
  cancelacion: "Cancelación",
  compra: "Compra",
  ajuste: "Ajuste",
};

export function StockMovesList({ product }: { product: Product }) {
  const { data, isLoading, error } = useProductMoves(product.id);

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return <p className="py-4 text-sm text-red-600">{error.message}</p>;
  }

  if (!data || data.length === 0) {
    return <p className="py-4 text-sm text-slate-500">Sin movimientos registrados.</p>;
  }

  return (
    <ul className="divide-y divide-slate-100">
      {data.map((move) => (
        <li key={move.id} className="flex items-center justify-between gap-4 py-3">
          <div>
            <p className="text-sm font-medium text-slate-800">
              <span className={move.quantity >= 0 ? "text-emerald-600" : "text-red-600"}>
                {move.quantity >= 0 ? `+${move.quantity}` : move.quantity}
              </span>{" "}
              → {move.stock_after} {product.unit}
            </p>
            <p className="text-xs text-slate-500">
              {move.reason ?? "Sin motivo"}
              {move.ref_type ? ` · ${refLabels[move.ref_type] ?? move.ref_type}` : ""}
            </p>
          </div>
          <time className="text-xs text-slate-400">{formatDateTime(move.created_at)}</time>
        </li>
      ))}
    </ul>
  );
}