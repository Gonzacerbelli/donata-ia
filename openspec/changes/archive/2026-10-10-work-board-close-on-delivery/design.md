# Design

## Context

Ver `proposal.md` — Why. Estado as-built relevante:

- `list_board` (`backend/app/repositories/work_items.py:61-101`) arma el tablero con una agregación:
  `$match` sobre `sales` con `status != "cancelado"`, `$lookup` a `work_items`, `$addFields` de
  defaults y `$sort` por `date`. Un único `$match` define el alcance del tablero.
- `update_sale` (`backend/app/services/sales.py:170-210`) es el único punto donde cambia el estado de
  cumplimiento (la creación de venta siempre arranca `pendiente`; el MCP usa `update_sale` para
  cancelar). Ahí convive el ajuste de stock al cancelar/reactivar (R4).
- `_get_open_sale` (`backend/app/services/work.py:43-47`) rechaza con `404` las ventas inexistentes o
  canceladas (unicidad: ninguna otra validación de ObjectId para `work-items`).
- `work_repo.upsert` ya es atómico con `$set`/`$setOnInsert`; sólo cambia los campos que recibe, por
  lo que se puede usar para apuntar `status` sin tocar prioridad/asignación/comentarios.

## Goals / Non-Goals

**Goals:**

- Que el tablero sólo liste órdenes no entregadas ni canceladas.
- Que entregar la orden cierre su tarjeta automáticamente (y reabrirla la devuelva a `pendiente`),
  sin perder prioridad, asignación ni comentarios.
- Congelar las tarjetas de órdenes entregadas (lectura del tablero únicamente).
- Mantener la regla unidireccional: el trabajo jamás entrega la orden.

**Non-Goals:**

- No tocar el frontend (el tablero se puebla del backend; la columna `terminado` sigue mostrando
  tarjetas marcadas a mano de órdenes no entregadas).
- No persistir saldos, no mover stock, no cambiar el modelo `Sale`.
- No exponer herramientas MCP nuevas ni añadir notificaciones.

## Decisions

1. **El alcance del tablero cambia en el `$match` inicial de `list_board`.**
   `{"status": {"$ne": "cancelado"}}` → `{"status": {"$nin": ["cancelado", "entregado"]}}`. Es un
   cambio de un operador: las órdenes entregadas nunca entran a la agregación, con o sin registro.

2. **La sincronización se dispara desde `update_sale` (única puerta del estado de cumplimiento).**
   En `services/sales.py`, dentro del bloque de cambio de estado, al escribir la venta:
   - si `body.status == "entregado"` → `work_service.mark_delivered(db, sale_id)` (upsert
     `status: "terminado"`);
   - si el estado anterior era `entregado` (y el nuevo no) → `work_service.mark_reopened(db, sale_id)`
     (upsert `status: "pendiente"`, preserva el resto de los campos).
   Cualquier otra transición no invoca helpers. Se llama después de persistir la venta; si el cambio
   de venta falla, la tarjeta no se toca.

3. **Helpers de dominio en `services/work.py`, reutilizando `upsert` del repository.**
   `mark_delivered` y `mark_reopened` sólo fijan `status` vía `work_repo.upsert`, que es idempotente
   y atómico; así el primer cierre crea el registro `terminado` y una reapertura no pisa prioridad,
   asignación ni comentarios. Importar `services.work` desde `services.sales` no genera ciclo:
   `work` no importa `services.sales`.

4. **Tarjetas de órdenes entregadas congeladas en `_get_open_sale`.**
   El `404` actual para canceladas se amplía también a `entregado`: `PATCH` y comentarios responden
   el mismo `NotFoundError` y la tarjeta no se modifica. Coherente con el tablero, que no las muestra.

5. **La regla inversa queda protegida por el diseño, no por código nuevo.**
   Ningún camino de `work-items` toca `sales`; el test "tarjeta terminada no entrega la orden" fija
   el requisito y evita regresiones.

## Risks / Trade-offs

- [Reapertura de una orden entregada devuelve la tarjeta a `pendiente`] → decisión del negocio:
  al reabrir, el trabajo vuelve a la cola; se conservan prioridad, asignación y comentarios.
- [Un `PATCH /sales` con `status=entregado` ahora escribe una tarjeta extra] → acotado: un único
  upsert idempotente; la venta queda como única fuente del estado de cumplimiento.
- [Venta entregada con registro previo queda "terminado" aunque tuviera otro estado] → esperado; el
  cierre automático sobreescribe el estado de trabajo al entregar.

## Migration Plan

Aditivo y sin datos que migrar: la sincronización sólo escribe `work_items` (colección 1:1 creada
por upsert). Rollback = revertir el commit; una tarjeta entregada ya escrita queda `terminado` sin
efecto colateral.

## Open Questions

<!-- ninguna -->