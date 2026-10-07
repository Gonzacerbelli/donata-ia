import { PageHeader } from "@/components/common/PageHeader";
import { useAuth } from "@/features/auth/useAuth";

export function DashboardPage() {
  const { user } = useAuth();
  const name = user?.name ?? user?.email ?? "";

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Resumen de la operación de Donata."
      />
      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <p className="text-sm text-slate-700">
          Hola{name ? `, ${name}` : ""} 👋
        </p>
        <p className="mt-2 text-sm text-slate-500">
          Los indicadores, el chat con IA y los módulos de negocio se habilitan en las próximas
          etapas.
        </p>
      </div>
    </div>
  );
}