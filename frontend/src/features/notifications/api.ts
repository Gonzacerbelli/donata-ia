import { api } from "@/lib/http";
import type { NotificationList } from "@/types/domain";

export interface NotificationUpdateInput {
  read?: boolean;
  dismissed?: boolean;
}

export const notificationsApi = {
  async list(): Promise<NotificationList> {
    const { data } = await api.get<NotificationList>("/notifications");
    return data;
  },
  async update(id: string, body: NotificationUpdateInput): Promise<NotificationList> {
    const { data } = await api.patch<NotificationList>(`/notifications/${id}`, body);
    return data;
  },
  async readAll(): Promise<NotificationList> {
    const { data } = await api.post<NotificationList>("/notifications/read-all");
    return data;
  },
  async dismissAll(): Promise<NotificationList> {
    const { data } = await api.post<NotificationList>("/notifications/dismiss-all");
    return data;
  },
};