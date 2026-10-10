# Proposal

## Why

Hoy el tablero de trabajo muestra como tarjetas todas las órdenes no canceladas, entonces una orden
marcada como `entregado` sigue apareciendo como tarea pendiente y obliga a repetir un cierre manual.
El estado de cumplimiento (`entregado`) debe ser la fuente: al entregar la orden, la tarjeta de
trabajo se cierra automáticamente, y el tablero deja de mostrar las órdenes ya entregadas.

## What Changes

- El tablero (`GET /work-items`) pasa a mostrar **sólo las órdenes no entregadas ni canceladas**;
  una orden con estado `entregado` no aparece más aunque tenga registro de trabajo.
- `PATCH /sales/{id}` con `status: "entregado"` cierra la tarjeta de trabajo de esa orden: su estado
  pasa a `terminado` de forma automática (se crea el registro por upsert si no existía).
- Si la orden vuelve de `entregado` a otro estado de cumplimiento, la tarjeta vuelve a `pendiente`
  conservando prioridad, asignación y comentarios.
- Cambios de cumplimiento que no entran ni salen de `entregado` (p. ej. `pendiente` → `en_proceso`)
  no tocan la tarjeta.
- Las tarjetas de órdenes entregadas quedan **congeladas**: `PATCH /work-items/{sale_id}` y
  `POST /work-items/{sale_id}/comments` responden `404`.
- La regla **no aplica al revés**: marcar una tarjeta como `terminado` jamás cambia el estado de
  cumplimiento de la orden.

## Capabilities

- **Modified Capabilities**:
  - `work-board`: cambia el alcance del tablero (excluye `entregado`), agrega el cierre/reapertura
    automáticos por estado de cumplimiento, congela las tarjetas de órdenes entregadas y refuerza la
    independencia con el escenario explícito "tarjeta terminada no entrega la orden".

## Impact

- **Backend**: `backend/app/repositories/work_items.py` (filtro del tablero), `backend/app/services/work.py`
  (helpers de cierre/reapertura y validación de tarjetas entregadas) y `backend/app/services/sales.py`
  (hook que sincroniza la tarjeta al cambiar el estado de cumplimiento).
- **Tests**: `backend/tests/test_work_items.py` (nuevos escenarios de exclusión, cierre, reversión,
  congelado y regla inversa).
- **Frontend**: sin cambios de código (el tablero ya se puebla del backend; la columna `terminado`
  seguirá mostrando tarjetas marcadas a mano de órdenes no entregadas).
- **Docs**: `docs/ARQUITECTURA.md` (regla R15), `docs/PLAN-IMPLEMENTACION.md` (estado del módulo),
  `README.md` (contadores de tests); `docs/CASOS_DE_USO.md` queda sin modificar.