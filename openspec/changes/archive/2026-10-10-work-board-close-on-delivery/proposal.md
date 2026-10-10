# Proposal

## Why

Hoy el tablero de trabajo muestra como tarjetas todas las �rdenes no canceladas, entonces una orden
marcada como `entregado` sigue apareciendo como tarea pendiente y obliga a repetir un cierre manual.
El estado de cumplimiento (`entregado`) debe ser la fuente: al entregar la orden, la tarjeta de
trabajo se cierra autom�ticamente, y el tablero deja de mostrar las �rdenes ya entregadas.

## What Changes

- El tablero (`GET /work-items`) pasa a mostrar **s�lo las �rdenes no entregadas ni canceladas**;
  una orden con estado `entregado` no aparece m�s aunque tenga registro de trabajo.
- `PATCH /sales/{id}` con `status: "entregado"` cierra la tarjeta de trabajo de esa orden: su estado
  pasa a `terminado` de forma autom�tica (se crea el registro por upsert si no exist�a).
- Si la orden vuelve de `entregado` a otro estado de cumplimiento, la tarjeta vuelve a `pendiente`
  conservando prioridad, asignaci�n y comentarios.
- Cambios de cumplimiento que no entran ni salen de `entregado` (p. ej. `pendiente` ? `en_proceso`)
  no tocan la tarjeta.
- Las tarjetas de �rdenes entregadas quedan **congeladas**: `PATCH /work-items/{sale_id}` y
  `POST /work-items/{sale_id}/comments` responden `404`.
- La regla **no aplica al rev�s**: marcar una tarjeta como `terminado` jam�s cambia el estado de
  cumplimiento de la orden.

## Capabilities

- **Modified Capabilities**:
  - `work-board`: cambia el alcance del tablero (excluye `entregado`), agrega el cierre/reapertura
    autom�ticos por estado de cumplimiento, congela las tarjetas de �rdenes entregadas y refuerza la
    independencia con el escenario expl�cito "tarjeta terminada no entrega la orden".

## Impact

- **Backend**: `backend/app/repositories/work_items.py` (filtro del tablero), `backend/app/services/work.py`
  (helpers de cierre/reapertura y validaci�n de tarjetas entregadas) y `backend/app/services/sales.py`
  (hook que sincroniza la tarjeta al cambiar el estado de cumplimiento).
- **Tests**: `backend/tests/test_work_items.py` (nuevos escenarios de exclusi�n, cierre, reversi�n,
  congelado y regla inversa).
- **Frontend**: sin cambios de c�digo (el tablero ya se puebla del backend; la columna `terminado`
  seguir� mostrando tarjetas marcadas a mano de �rdenes no entregadas).
- **Docs**: `docs/ARQUITECTURA.md` (regla R15), `docs/PLAN-IMPLEMENTACION.md` (estado del m�dulo),
  `README.md` (contadores de tests); `docs/CASOS_DE_USO.md` queda sin modificar.