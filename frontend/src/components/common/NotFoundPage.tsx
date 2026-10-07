import { Link } from "react-router-dom";

import { Button } from "@/components/ui/Button";

export function NotFoundPage() {
  return (
    <main className="flex min-h-full flex-col items-center justify-center gap-4 px-4 py-12 text-center">
      <h1 className="text-2xl font-semibold text-slate-900">Página no encontrada</h1>
      <p className="text-sm text-slate-500">La dirección a la que intentaste acceder no existe.</p>
      <Link to="/dashboard">
        <Button variant="secondary">Ir al dashboard</Button>
      </Link>
    </main>
  );
}