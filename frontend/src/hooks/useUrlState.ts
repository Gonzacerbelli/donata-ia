import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";

export function useUrlState() {
  const [params, setParams] = useSearchParams();

  const update = useCallback(
    (patch: Record<string, string | undefined>) => {
      setParams(
        (previous) => {
          const next = new URLSearchParams(previous);
          for (const [key, value] of Object.entries(patch)) {
            if (value === undefined || value === "") next.delete(key);
            else next.set(key, value);
          }
          return next;
        },
        { replace: true },
      );
    },
    [setParams],
  );

  return { params, update };
}