import { cn } from "@/lib/utils";

interface SpinnerProps {
  className?: string;
  label?: string;
}

export function Spinner({ className, label = "Cargando" }: SpinnerProps) {
  return (
    <span role="status" aria-label={label} className={cn("inline-flex", className)}>
      <span className="size-5 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
    </span>
  );
}