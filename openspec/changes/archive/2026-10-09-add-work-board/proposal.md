# Proposal

## Why

El negocio necesita dar seguimiento al trabajo operativo de cada pedido - qui�n lo toma, en qu�
estado est�, con qu� prioridad y con qu� notas - y hoy no existe: las �rdenes s�lo tienen estado
de cumplimiento y estado de cobranza, sin asignaci�n, prioridad ni comentarios, as� que la
coordinaci�n entre quienes usan el sistema (login local o SSO de Google) queda fuera de la
aplicaci�n. Construirlo ahora, apoyado en `sales`, elimina el seguimiento por fuera del sistema y
aporta una vista de tablero que organiza el trabajo diario. Es un m�dulo nuevo fuera de los 10 CU
validados; se apoya en CU05 (�rdenes) sin modificarlo.

## What Changes

- Nuevo m�dulo **"Trabajo"** en la barra lateral: todas las �rdenes **no canceladas** como
  tarjetas, agrupadas en cuatro columnas de **estado de trabajo**: `pendiente`, `en_curso`,
  `bloqueado` y `terminado`.
- Cada tarjeta muestra el **resumen de productos**, la **fecha del pedido**, la **prioridad**, el
  **usuario asignado** y sus **comentarios**.
- **Drag & drop** entre columnas para cambiar el estado de trabajo; agrega la dependencia
  `@dnd-kit/core`. No es **BREAKING**: no cambia contratos existentes.
- **Prioridad** `alta | media | baja` y **asignaci�n a cualquier usuario activo**; **comentarios**
  append-only con autor y fecha.
- **Filtros y orden** por fecha del pedido (ascendente/descendente), prioridad y usuario asignado,
  con el estado del tablero en la URL.
- Backend: nueva colecci�n `work_items` (1:1 con `sales`, creada por *upsert*), endpoints
  `GET /work-items`, `PATCH /work-items/{sale_id}`, `POST /work-items/{sale_id}/comments`, y
  `GET /users` (directorio de usuarios activos para el selector de asignaci�n).
- **Fuera de alcance:** no se modifica el estado de cumplimiento (`Sale.status`) ni la cobranza de
  la venta; no se exponen herramientas MCP del tablero al asistente; sin tiempo real ni websockets;
  sin paginaci�n; sin orden manual dentro de una columna; no se toca `docs/CASOS_DE_USO.md`.

## Capabilities

### New Capabilities

- `work-board`: tablero de trabajo sobre las �rdenes - columnas por estado de trabajo,
  priorizaci�n, asignaci�n, comentarios, filtros/orden y cambio de estado por drag & drop.
- `user-directory`: listado de usuarios activos del sistema para asignar tarjetas y filtrar por
  usuario asignado (sin roles ni permisos).

### Modified Capabilities

<!-- ninguna: el tablero no cambia el comportamiento especificado de las capacidades existentes;
     `order-management` se lee (�rdenes no canceladas) pero sus requisitos no cambian. -->

## Impact

- **Backend:** `models/domain.py` + `models/__init__.py` (`WorkItem`, `WorkComment`),
  `schemas/entities.py` (`WorkItemUpdate`, `CommentCreate`) y `schemas/auth.py` (`UserSummary`),
  `repositories/work_items.py` y `repositories/users.py` (nuevos), `services/work.py` (nuevo),
  `routers/work.py` y `routers/users.py` (nuevos), `db.py` (�ndices de `work_items`),
  `main.py` (registro de routers).
- **Frontend:** `package.json` (+ `@dnd-kit/core`), `routes/paths.ts`,
  `components/layout/Sidebar.tsx`, `app/router.tsx`, `features/work-board/**` (nuevo),
  `types/domain.ts`.
- **Tests:** `backend/tests/test_work_items.py`, `backend/tests/test_users.py`; tests Vitest del
  feature y `frontend/e2e/trabajo.spec.ts`.
- **Docs:** `docs/PLAN-IMPLEMENTACION.md` (estado de la fase), `docs/ARQUITECTURA.md` (�3.1
  colecciones y regla de negocio nueva) y bit�cora de `README`. `docs/CASOS_DE_USO.md` **no se
  modifica**: el m�dulo se documenta como extensi�n fuera de los CU validados.
