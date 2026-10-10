# Design

## Context

Ver `proposal.md` — Why. Estado as-built relevante:

- El backend está en capas `routers/ → services/ → repositories/`; los routers sólo traducen HTTP y
  toda query vive en el repository (`backend/AGENTS.md` §65-74). `get_current_user` devuelve el
  `User` completo y los routers lo aplican a nivel de router (`backend/app/dependencies.py:16-34`).
- `Sale` ya tiene un eje de cumplimiento (`status`) y uno de cobranza derivado del saldo; el módulo
  agrega un **tercer eje independiente** (trabajo), sin tocar los otros dos (invariante R4).
- No existe ningún concepto de asignación, prioridad ni comentarios en el repo; tampoco hay
  drag & drop ni dependencias de DnD en el frontend.
- El frontend organiza por *feature*, usa TanStack Query para estado de servidor y guarda los
  filtros en la URL (`frontend/AGENTS.md` §38-50); el sidebar es un array plano de ítems
  (`frontend/src/components/layout/Sidebar.tsx:6-12`).

## Goals / Non-Goals

**Goals:**

- Representar el seguimiento de trabajo de una orden sin modificar su entidad validada.
- Un tablero que liste todas las órdenes no canceladas con filtros/orden del lado del servidor.
- Cambiar de estado por drag & drop, además de editar prioridad, asignación y comentarios.
- Mantener el tablero consistente y testeable con los patrones ya existentes (pytest + Vitest +
  Playwright).

**Non-Goals:**

- No exponer el tablero como tools MCP del asistente.
- No agregar tiempo real, paginación ni orden manual dentro de una columna.
- No reutilizar ni renombrar los estados de cumplimiento de la venta.
- No introducir roles ni permisos: cualquier usuario con JWT gestiona cualquier tarjeta.

## Decisions

1. **Colección `work_items` 1:1 con `sales`, en lugar de campos en `Sale`.**
   Alternativa considerada: agregar `work_status`, `priority`, `assigned_to` y `comments[]` a
   `sales`. Se descarta porque mezcla el ciclo de vida validado de la orden (CU05) con un concepto
   nuevo y obliga a tocar el modelo y la spec as-built de órdenes. La colección propia aísla los
   índices y los ejes de filtrado, y permite que una orden no tenga registro de trabajo (defaults).

2. **El tablero se arma con una agregación `$lookup` en el repository.**
   `list_board` parte de `sales` filtrando `status != "cancelado"`, hace `$lookup` a `work_items`
   por `sale_id`, usa `$addFields` para coalescer los defaults (`pendiente`, `media`, sin
   asignado) cuando no hay registro, aplica el `$match` de filtros (prioridad, asignado), agrega un
   campo de rango para prioridad y ordena por `date` asc/desc. La agregación vive en
   `repositories/work_items.py` (regla: toda query en el repository).

3. **Cambios por *upsert* idempotente.** `PATCH /work-items/{sale_id}` valida que la venta exista y
   no esté cancelada (`404` si no), y hace `updateOne({sale_id}, {$set: {...}, $setOnInsert: {...}},
   upsert=True)`. Así el primer cambio crea el registro con los defaults y no hay carrera entre
   lectura y escritura. Se descarta "crear la tarjeta primero" porque el tablero ya lista todas las
   órdenes.

4. **Estados y prioridad como `Literal` de Pydantic.** `status ∈ {pendiente, en_curso, bloqueado,
   terminado}` y `priority ∈ {alta, media, baja}` → `422` automático, sin validación manual.

5. **`assigned_to` y el autor del comentario como `ObjIdStr` (ObjectId), con snapshot del nombre.**
   Se sigue el patrón de `ChatThread.user_id`. El comentario guarda `author_id` + `author_name`
   copiado al crear (igual que `unit_price` resuelto en la venta: la historia no cambia si el
   usuario se renombra). `assigned_to` se valida contra un usuario **activo** antes de persistir.

6. **Directorio de usuarios como router propio `GET /users`.** Devuelve `id`, `name`, `email` de
   los activos (`UserSummary`), sólo para poblar el selector y el filtro. No implica roles.

7. **Drag & drop con `@dnd-kit/core` (dependencia nueva, aprobada).** Sólo `core`: las columnas son
   droppables y las tarjetas draggables; no hace falta `sortable` porque no hay reordenamiento
   dentro de la columna. Alternativa descartada: HTML5 DnD nativo (peor accesibilidad y manejo de
   touch).

8. **Filtros del tablero en la URL** (`sort`, `priority`, `assigned`) con `useUrlFilters`, y claves
   de TanStack Query `workKeys`; cada mutación invalida `workKeys.all`. Las tarjetas reutilizan el
   resumen de `items` que ya devuelve la orden.

9. **Índices en `db.py`:** `work_items.sale_id` (único), `work_items.status`,
   `work_items.priority`, `work_items.assigned_to`.

10. **Seguridad.** `get_current_user` en todos los endpoints del tablero y de usuarios; validación
    de ObjectId (id inválido → `404`, nunca `500`); texto de comentario acotado
    (`max_length=2000`) y renderizado como texto (sin `dangerouslySetInnerHTML`).

**Invariantes de negocio:** no se persiste ningún saldo (el tablero no toca cobranza); no se
modifica stock (el trabajo no descuenta ni restituye); no hay roles (sólo usuario activo/inactivo);
fechas en UTC; el trabajo es un eje independiente del cumplimiento y la cobranza.

## Risks / Trade-offs

- [`@dnd-kit/core` no se testea bien en jsdom] → el drag & drop se cubre con Playwright; en Vitest
  se testean funciones puras y componentes sin drag (con los hooks mockeados).
- [`$lookup` sobre todas las órdenes no canceladas puede crecer] → índice único en `work_items.sale_id`
  y `$match` temprano en `sales`; la paginación queda fuera de alcance y se documenta.
- [Carrera al crear el registro en el primer cambio] → *upsert* atómico con `$setOnInsert`.
- [Cancelar una orden hace desaparecer la tarjeta] → decisión deliberada: el tablero muestra sólo
  no canceladas; el registro de trabajo se conserva por si la orden se reactiva.
- [Referencias a usuario renombrado/inactivo en comentarios] → snapshot de `author_name` y sólo se
  valida actividad al asignar, no al leer.

## Migration Plan

Aditivo: no hay migración de datos ni cambios de contrato existente. La colección `work_items` se
crea por *upsert*; los índices se crean en `init_indexes` al arrancar. Rollback = revertir el commit
(la colección queda huérfana, sin efecto, y puede eliminarse manualmente).

## Open Questions

<!-- ninguna -->
