# Tasks

## 1. Backend — modelos, índices y repositorios

- [x] 1.1 Crear `WorkItem` y `WorkComment` en `backend/app/models/domain.py`, exportarlos en `models/__init__.py` y agregar los índices de `work_items` (unique `sale_id`, `status`, `priority`, `assigned_to`) en `backend/app/db.py` — verificar con un test que inserta y relee un registro y con la creación de índices en el fixture.
- [x] 1.2 Implementar `backend/app/repositories/work_items.py` con `get_by_sale`, `upsert` (con `$setOnInsert`), `add_comment` y `list_board` (agregación `$lookup` + defaults `pendiente`/`media`/sin asignar + filtros de prioridad/asignado + orden por `date` asc/desc) — verificar con tests de repositorio: lista con y sin registro, exclusión de órdenes canceladas y orden por fecha.
- [x] 1.3 Implementar `list_active` en `backend/app/repositories/users.py` (id, nombre, email de usuarios activos) — verificar con un test de repositorio que excluye los inactivos.

## 2. Backend — API del tablero y directorio de usuarios (TDD)

- [x] 2.1 Definir `WorkItemUpdate` y `CommentCreate` en `backend/app/schemas/entities.py` y `UserSummary` en `backend/app/schemas/auth.py`, y `backend/app/services/work.py` con la validación de estado/prioridad y de usuario activo (`422`) y `404` si la venta no existe o está cancelada — verificar con tests unitarios del servicio para cada regla.
- [x] 2.2 Crear `backend/app/routers/work.py` con `GET /work-items` (filtros `status`, `priority`, `assigned_to` combinables y `date_sort` asc/desc) y registrarlo en `main.py` — verificar con tests de integración (`auth_client`): listado, filtros combinados, orden por fecha y `401` sin token.
- [x] 2.3 Agregar `PATCH /work-items/{sale_id}` (upsert de estado, prioridad y asignación) que responde `422` ante valores inválidos y `404` ante una venta inexistente o cancelada — verificar con tests de integración que además comprueban que el estado de cumplimiento, los pagos y el stock de la orden no cambian.
- [x] 2.4 Agregar `POST /work-items/{sale_id}/comments` (comentario append-only con autor y fecha; `422` con texto vacío) — verificar con tests de integración que el comentario queda con el autor de la sesión y que el texto vacío no se persiste.
- [x] 2.5 Crear `backend/app/routers/users.py` con `GET /users` (activos con id/nombre/email) y registrarlo en `main.py` — verificar con tests de integración que excluye inactivos y responde `401` sin token.

## 3. Frontend — base del feature y tablero

- [x] 3.1 Agregar la dependencia `@dnd-kit/core`, la ruta `trabajo` en `src/routes/paths.ts`, el ítem "Trabajo" en `src/components/layout/Sidebar.tsx` y la ruta `/trabajo` en `src/app/router.tsx` — verificar con `npm install`, `npx tsc --noEmit` y que el enlace "Trabajo" navega a la página.
- [x] 3.2 Crear `src/features/work-board/{types.ts,api.ts,hooks.ts}` (tablero, cambio de trabajo, comentarios y `usersApi.list`) y los tipos nuevos en `src/types/domain.ts` con sus claves `workKeys` — verificar con `npx tsc --noEmit` y un test unitario de `api` con el cliente axios mockeado.
- [x] 3.3 Implementar `WorkBoardPage` con las cuatro columnas y la tarjeta (resumen de `items`, fecha del pedido, prioridad, asignado) cubriendo loading/empty/error/data — verificar con un test de componente en Vitest con los hooks mockeados.
- [x] 3.4 Integrar el drag & drop entre columnas con `@dnd-kit/core` para cambiar el estado (`PATCH`) e invalidar `workKeys` — verificar con `npx tsc --noEmit` y `npm run lint` (el drag se cubre en E2E).
- [x] 3.5 Agregar los filtros/orden en la URL (`sort`, `priority`, `assigned`) con `useUrlFilters`, el `PriorityBadge`, el `AssigneeSelect` y el `CommentModal` — verificar con tests unitarios de los helpers de filtro y del badge, y con `npm run lint`.

## 4. Integración, documentación y verificación end-to-end

- [x] 4.1 Escribir `frontend/e2e/trabajo.spec.ts` (login → "Trabajo" → arrastrar una tarjeta y ver el estado persistido → agregar un comentario → filtrar por prioridad) — verificar con `npx playwright test`.
- [x] 4.2 Actualizar `docs/PLAN-IMPLEMENTACION.md` (estado del módulo), `docs/ARQUITECTURA.md` (§3.1 colección `work_items` y la regla nueva) y la bitácora de `README.md`; no tocar `docs/CASOS_DE_USO.md` — verificar con `git grep` de los cambios y de que `CASOS_DE_USO.md` queda sin modificar.
- [x] 4.3 Correr la verificación completa del backend: `docker compose run --rm --no-deps api sh -c 'ruff format app tests scripts; ruff check app tests scripts; python -m pytest -q'` — verificar con salida en 0 y sin fallos. Resultado: `212 passed`.
- [x] 4.4 Correr la verificación completa del frontend: `npm test; npx tsc --noEmit; npm run lint; npm run build; npx playwright test` — verificar con 0 fallos en cada comando y el E2E existente (9/9) aún verde. Resultado: Vitest `54/54`, `tsc`/`lint`/`build` sin errores y Playwright `10/10` luego de ajustar selectores del spec nuevo (exact match, `.last()`, nota única con timestamp).

## Workflow follow-up

- Archivar el change con `/opsx-archive` una vez cumplidos los requisitos de revisión, para que los requirements aterricen en `openspec/specs/work-board/spec.md` y `openspec/specs/user-directory/spec.md`.
- Commitear la implementación sólo cuando el usuario lo autorice.
