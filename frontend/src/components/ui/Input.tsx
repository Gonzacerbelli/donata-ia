import { forwardRef, type InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, className, id, ...props },
  ref,
) {
  const inputId = id ?? props.name;
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={inputId} className="text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      <input
        id={inputId}
        ref={ref}
        aria-invalid={Boolean(error)}
        className={cn(
          "rounded-lg bg-white px-3 py-2 text-sm text-slate-900 ring-1 ring-inset transition",
          "focus:outline-none focus:ring-2",
          error
            ? "ring-red-400 focus:ring-red-500"
            : "ring-slate-300 focus:ring-brand-600",
          className,
        )}
        {...props}
      />
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
});