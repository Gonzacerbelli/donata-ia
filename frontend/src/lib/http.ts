import axios, { type AxiosError } from "axios";

import { tokenStore } from "./token";

export class ApiError extends Error {
  status: number;
  retryAfter?: number;

  constructor(message: string, status: number, retryAfter?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.retryAfter = retryAfter;
  }
}

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

let unauthorizedHandler: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function messageFor(status: number, detail?: string): string {
  if (status === 401) return detail ?? "Tu sesión expiró. Volvé a iniciar sesión.";
  if (status === 403) return detail ?? "No tenés permiso para hacer esta acción.";
  if (status === 404) return detail ?? "No encontramos el recurso.";
  if (status === 409) return detail ?? "La operación entra en conflicto con datos existentes.";
  if (status === 422) return detail ?? "Los datos enviados no son válidos.";
  if (status === 429) return detail ?? "Demasiadas solicitudes. Esperá un momento.";
  if (status >= 500) return "El servicio no está disponible. Intentá de nuevo.";
  return detail ?? "Ocurrió un error inesperado.";
}

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const status = error.response?.status ?? 0;
    const detail = error.response?.data?.detail;

    if (status === 401) {
      tokenStore.clear();
      unauthorizedHandler?.();
    }

    let retryAfter: number | undefined;
    if (status === 429) {
      const header = error.response?.headers?.["retry-after"];
      const parsed = Number(header);
      retryAfter = Number.isFinite(parsed) ? parsed : undefined;
    }

    const message = status === 0 ? "No pudimos conectar con el servidor." : messageFor(status, detail);
    return Promise.reject(new ApiError(message, status, retryAfter));
  },
);