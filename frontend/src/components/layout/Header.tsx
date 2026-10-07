import { Button } from "@/components/ui/Button";
import { useAuth } from "@/features/auth/useAuth";
import { NotificationBell } from "@/features/notifications/components/NotificationBell";

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
      <span className="text-sm font-semibold text-brand-700 md:hidden">Donata IA</span>
      <div className="hidden md:block" />
      <div className="flex items-center gap-3">
        <NotificationBell />
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