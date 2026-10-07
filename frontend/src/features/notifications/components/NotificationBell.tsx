import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Spinner } from "@/components/ui/Spinner";
import type { AppNotification, NotificationSeverity } from "@/types/domain";

import { useDismissAll, useMarkAllRead, useNotifications, useUpdateNotification } from "../hooks";

const severityStyles: Record<NotificationSeverity, string> = {
  alta: "border-l-red-500",
  media: "border-l-amber-500",
  baja: "border-l-slate-300",
};

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const { data, isLoading, error } = useNotifications();
  const updateNotification = useUpdateNotification();
  const markAllRead = useMarkAllRead();
  const dismissAll = useDismissAll();

  const items = data?.items ?? [];
  const unread = data?.unread_count ?? 0;

  function openItem(notification: AppNotification) {
    if (!notification.read) {
      updateNotification.mutate({ id: notification.id, body: { read: true } });
    }
    setOpen(false);
    if (notification.entity === "sale") {
      navigate(`/ordenes/${notification.entity_id}`);
    } else {
      navigate("/productos");
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        aria-label="Notificaciones"
        onClick={() => setOpen((value) => !value)}
        className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100"
      >
        <span aria-hidden="true" className="text-lg leading-none">
          🔔
        </span>
        {unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
            {unread > 99 ? "99+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-30 mt-2 w-80 rounded-xl border border-slate-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2">
            <span className="text-sm font-semibold text-slate-800">Notificaciones</span>
            <div className="flex gap-2 text-xs">
              <button
                type="button"
                className="font-medium text-brand-600 hover:underline disabled:text-slate-300"
                disabled={unread === 0 || markAllRead.isPending}
                onClick={() => markAllRead.mutate()}
              >
                Marcar leídas
              </button>
              <button
                type="button"
                className="font-medium text-slate-500 hover:underline disabled:text-slate-300"
                disabled={items.length === 0 || dismissAll.isPending}
                onClick={() => dismissAll.mutate()}
              >
                Descartar todo
              </button>
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : error ? (
              <p className="px-4 py-6 text-sm text-red-600">{error.message}</p>
            ) : items.length === 0 ? (
              <p className="px-4 py-6 text-sm text-slate-500">No hay notificaciones.</p>
            ) : (
              <ul className="divide-y divide-slate-100">
                {items.map((notification) => (
                  <li
                    key={notification.id}
                    className={`border-l-4 ${severityStyles[notification.severity]} ${
                      notification.read ? "bg-white" : "bg-brand-50/40"
                    }`}
                  >
                    <div className="flex items-start gap-2 px-4 py-3">
                      <button
                        type="button"
                        className="flex-1 text-left"
                        onClick={() => openItem(notification)}
                      >
                        <p className="text-sm font-medium text-slate-800">{notification.title}</p>
                        <p className="mt-0.5 text-xs text-slate-500">{notification.description}</p>
                      </button>
                      <button
                        type="button"
                        aria-label="Descartar"
                        title="Descartar"
                        className="text-slate-300 hover:text-slate-600"
                        onClick={() =>
                          updateNotification.mutate({
                            id: notification.id,
                            body: { dismissed: true },
                          })
                        }
                      >
                        ✕
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}