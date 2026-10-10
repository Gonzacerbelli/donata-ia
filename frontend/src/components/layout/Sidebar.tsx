import { NavLink } from "react-router-dom";

import { cn } from "@/lib/utils";
import { paths } from "@/routes/paths";

const items = [
  { to: paths.dashboard, label: "Dashboard" },
  { to: paths.providers, label: "Proveedores" },
  { to: paths.products, label: "Productos" },
  { to: paths.clients, label: "Clientes" },
  { to: paths.orders, label: "Órdenes" },
  { to: paths.work, label: "Trabajo" },
];

export function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-slate-200 bg-white px-3 py-6 md:flex">
      <div className="px-3 pb-6">
        <span className="text-lg font-semibold text-brand-700">Donata IA</span>
      </div>
      <nav className="flex flex-col gap-1" aria-label="Navegación principal">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
              )
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}