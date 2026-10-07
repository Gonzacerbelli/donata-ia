import { Button } from "@/components/ui/Button";
import { useAuth } from "@/features/auth/useAuth";

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
      <span className="text-sm font-semibold text-brand-700 md:hidden">Donata IA</span>
      <div className="hidden md:block" />
      <div className="flex items-center gap-3">
        <button
          type="button"
          aria-label="Notificaciones"
          title="Notificaciones (próximamente)"
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
        >
          <span aria-hidden="true" className="text-lg leading-none">
            🔔
          </span>
        </button>
        <div className="text-right">
          <p className="text-sm font-medium text-slate-800">{user?.name ?? user?.email ?? "Usuario"}</p>
        </div>
        <Button variant="ghost" size="sm" onClick={logout}>
          Salir
        </Button>
      </div>
    </header>
  );
}