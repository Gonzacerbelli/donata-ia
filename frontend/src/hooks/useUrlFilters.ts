import { useSearchParams } from "react-router-dom";

export function useUrlFilters(defaults: Record<string, string> = {}) {
  const [params, setParams] = useSearchParams();

  const get = (key: string) => params.get(key) ?? defaults[key] ?? "";

  const setParam = (key: string, value: string) => {
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        if (!value) next.delete(key);
        else next.set(key, value);
        return next;
      },
      { replace: true },
    );
  };

  return { params, get, setParam };
}