# Donata IA — Frontend

SPA en Vite + React 19 + TypeScript + Tailwind CSS v4. Consume la API del backend
(FastAPI) y el asistente IA.

## Requisitos

- Node.js 20+
- Backend corriendo (por defecto en `http://localhost:8000`)

## Puesta en marcha

```bash
npm install
cp .env.example .env
npm run dev
```

La variable `VITE_API_URL` apunta al backend.

## Scripts

| Script | Qué hace |
|---|---|
| `npm run dev` | Servidor de desarrollo (Vite) |
| `npm run build` | Chequeo de tipos + build de producción |
| `npm run preview` | Sirve el build de producción |
| `npm run lint` | ESLint |
| `npm test` | Vitest |

## Estructura

```
src/
  app/         providers (React Query + Auth) y router con guard
  components/  ui (Button, Input, Modal…), common (DataTable, estados) y layout
  features/    auth, dashboard (y en etapas siguientes: negocio, notificaciones, chat)
  lib/         http (Axios + interceptores), token, format, queryClient
  routes/      paths
  test/        setup de Vitest
```

Las convenciones de código y de UX están en [`AGENTS.md`](./AGENTS.md).