# Design

## Context

Ver `proposal.md` - Why. Estado as-built relevante:

- `list_board` (`backend/app/repositories/work_items.py:61-101`) arma el tablero con una agregaci�n:
  `$match` sobre `sales` con `status != "cancelado"`, `$lookup` a `work_items`, `$addFields` de
  defaults y `$sort` por `date`. Un �nico `$match` define el alcance del tablero.
- `update_sale` (`backend/app/services/sales.py:170-210`) es el �nico punto donde cambia el estado de
  cumplimiento (la creaci�n de venta siempre arranca `pendiente`; el MCP usa `update_sale` para
  cancelar). Ah� convive el ajuste de stock al cancelar/reactivar (R4).
- `_get_open_sale` (`backend/app/services/work.py:43-47`) rechaza con `404` las ventas inexistentes o
  canceladas (unicidad: ninguna otra validaci�n de ObjectId para `work-items`).
- `work_repo.upsert` ya es at�mico con `$set`/`$setOnInsert`; s�lo cambia los campos que recibe, por
  lo que se puede usar para apuntar `status` sin tocar prioridad/asignaci�n/comentarios.

## Goals / Non-Goals

**Goals:**

- Que el tablero s�lo liste �rdenes no entregadas ni canceladas.
- Que entregar la orden cierre su tarjeta autom�ticamente (y reabrirla la devuelva a `pendiente`),
  sin perder prioridad, asignaci�n ni comentarios.
- Congelar las tarjetas de �rdenes entregadas (lectura del tablero �nicamente).
- Mantener la regla unidireccional: el trabajo jam�s entrega la orden.

**Non-Goals:**

- No tocar el frontend (el tablero se puebla del backend; la columna `terminado` sigue mostrando
  tarjetas marcadas a mano de �rdenes no entregadas).
- No persistir saldos, no mover stock, no cambiar el modelo `Sale`.
- No exponer herramientas MCP nuevas ni a�adir notificaciones.

## Decisions

1. **El alcance del tablero cambia en el `$match` inicial de `list_board`.**
   `{"status": {"$ne": "cancelado"}}` ? `{"status": {"$nin": ["cancelado", "entregado"]}}`. Es un
   cambio de un operador: las �rdenes entregadas nunca entran a la agregaci�n, con o sin registro.

2. **La sincronizaci�n se dispara desde `update_sale` (�nica puerta del estado de cumplimiento).**
   En `services/sales.py`, dentro del bloque de cambio de estado, al escribir la venta:
   - si `body.status == "entregado"` ? `work_service.mark_delivered(db, sale_id)` (upsert
     `status: "terminado"`);
   - si el estado anterior era `entregado` (y el nuevo no) ? `work_service.mark_reopened(db, sale_id)`
     (upsert `status: "pendiente"`, preserva el resto de los campos).
   Cualquier otra transici�n no invoca helpers. Se llama despu�s de persistir la venta; si el cambio
   de venta falla, la tarjeta no se toca.

3. **Helpers de dominio en `services/work.py`, reutilizando `upsert` del repository.**
   `mark_delivered` y `mark_reopened` s�lo fijan `status` v�a `work_repo.upsert`, que es idempotente
   y at�mico; as� el primer cierre crea el registro `terminado` y una reapertura no pisa prioridad,
   asignaci�n ni comentarios. Importar `services.work` desde `services.sales` no genera ciclo:
   `work` no importa `services.sales`.

4. **Tarjetas de �rdenes entregadas congeladas en `_get_open_sale`.**
   El `404` actual para canceladas se ampl�a tambi�n a `entregado`: `PATCH` y comentarios responden
   el mismo `NotFoundError` y la tarjeta no se modifica. Coherente con el tablero, que no las muestra.

5. **La regla inversa queda protegida por el dise�o, no por c�digo nuevo.**
   Ning�n camino de `work-items` toca `sales`; el test "tarjeta terminada no entrega la orden" fija
   el requisito y evita regresiones.

## Risks / Trade-offs

- [Reapertura de una orden entregada devuelve la tarjeta a `pendiente`] ? decisi�n del negocio:
  al reabrir, el trabajo vuelve a la cola; se conservan prioridad, asignaci�n y comentarios.
- [Un `PATCH /sales` con `status=entregado` ahora escribe una tarjeta extra] ? acotado: un �nico
  upsert idempotente; la venta queda como �nica fuente del estado de cumplimiento.
- [Venta entregada con registro previo queda "terminado" aunque tuviera otro estado] ? esperado; el
  cierre autom�tico sobreescribe el estado de trabajo al entregar.

## Migration Plan

Aditivo y sin datos que migrar: la sincronizaci�n s�lo escribe `work_items` (colecci�n 1:1 creada
por upsert). Rollback = revertir el commit; una tarjeta entregada ya escrita queda `terminado` sin
efecto colateral.

## Open Questions

<!-- ninguna -->