import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { downloadExport, type DownloadParams } from "@/lib/api/download";
import { ApiError } from "@/lib/http";

type ExportEntity = "sales" | "clients" | "products";
type Format = "csv" | "xlsx";

interface ExportButtonsProps {
  entity: ExportEntity;
  params: DownloadParams;
  disabled?: boolean;
}

export function ExportButtons({ entity, params, disabled = false }: ExportButtonsProps) {
  const [pending, setPending] = useState<Format | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retryAfter, setRetryAfter] = useState(0);

  useEffect(() => {
    if (retryAfter <= 0) return;
    const timer = setInterval(() => setRetryAfter((value) => Math.max(0, value - 1)), 1000);
    return () => clearInterval(timer);
  }, [retryAfter]);

  async function handleExport(format: Format) {
    setError(null);
    setPending(format);
    try {
      await downloadExport(`/exports/${entity}.${format}`, params, `${entity}.${format}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        if (err.retryAfter) setRetryAfter(err.retryAfter);
      } else {
        setError("No pudimos generar la exportación.");
      }
    } finally {
      setPending(null);
    }
  }

  const blocked = disabled || retryAfter > 0;

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="secondary"
        size="sm"
        disabled={blocked}
        isLoading={pending === "csv"}
        onClick={() => handleExport("csv")}
      >
        Exportar CSV
      </Button>
      <Button
        variant="secondary"
        size="sm"
        disabled={blocked}
        isLoading={pending === "xlsx"}
        onClick={() => handleExport("xlsx")}
      >
        Exportar Excel
      </Button>
      {retryAfter > 0 && (
        <span className="text-xs text-amber-600">Esperá {retryAfter} s</span>
      )}
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  );
}