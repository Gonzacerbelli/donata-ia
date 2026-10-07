import { useEffect, useState } from "react";

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  delay?: number;
}

export function SearchInput({ value, onChange, placeholder, delay = 300 }: SearchInputProps) {
  const [local, setLocal] = useState(value);

  useEffect(() => {
    setLocal(value);
  }, [value]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (local !== value) onChange(local);
    }, delay);
    return () => clearTimeout(timer);
  }, [local, value, onChange, delay]);

  return (
    <input
      type="search"
      role="searchbox"
      value={local}
      placeholder={placeholder}
      onChange={(event) => setLocal(event.target.value)}
      className="w-full rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-900 ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-brand-600 focus:outline-none sm:w-72"
    />
  );
}