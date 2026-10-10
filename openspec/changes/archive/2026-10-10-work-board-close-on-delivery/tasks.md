# Tasks

## 1. Backend - alcance del tablero y congelado de tarjetas entregadas (TDD)

- [x] 1.1 Cambiar el `$match` inicial de `list_board` en `backend/app/repositories/work_items.py` de
  `status != "cancelado"` a `status ? {"cancelado", "entregado"} excluidos` - verificar con el test
  existente de cancelada y un test nuevo `test_board_excludes_delivered` que entrega la orden (con y
  sin registro de trabajo) y espera tablero vac�o.
- [x] 1.2 Ampliar `_get_open_sale` en `backend/app/services/work.py` para responder `404` tambi�n
  cuando la venta est� `entregado` - verificar con tests que `PATCH /work-items/{id}` y
  `POST /work-items/{id}/comments` sobre una orden entregada responden `404` y no modifican la tarjeta.

## 2. Backend - sincronizaci�n autom�tica con el estado de cumplimiento (TDD)

- [x] 2.1 Implementar `mark_delivered` y `mark_reopened` en `backend/app/services/work.py` usando
  `work_repo.upsert` (s�lo `status`) - verificar con tests de integraci�n que entregar una orden con
  tarjeta en `en_curso` la deja `terminado`, y que una sin registro crea la tarjeta `terminado`.
- [x] 2.2 Invocar la sincronizaci�n desde `update_sale` en `backend/app/services/sales.py` tras
  persistir: `entregado` ? `mark_delivered`; salida de `entregado` ? `mark_reopened` - verificar con
  tests que reabrir la orden devuelve la tarjeta a `pendiente` (conservando prioridad, asignaci�n y
  comentarios) y que `pendiente ? en_proceso` no toca la tarjeta.

## 3. Backend - regla inversa y verificaci�n completa

- [x] 3.1 Fijar la regla inversa con un test expl�cito: marcar la tarjeta como `terminado` deja el
  estado de cumplimiento de la orden sin cambios - verificar con `test_terminated_card_does_not_deliver_sale`
  (adem�s del `test_work_change_does_not_touch_sale` ya existente) y con `python -m py_compile`.
- [x] 3.2 Correr la verificaci�n completa del backend:
  `docker compose run --rm --no-deps api sh -c 'ruff format app tests scripts; ruff check app tests scripts; python -m pytest -q'`
  - verificar con salida en 0 y sin fallos (212 preexistentes + los nuevos). Resultado: `220 passed`.

## 4. Documentaci�n y verificaci�n de regresi�n

- [x] 4.1 Actualizar `docs/ARQUITECTURA.md` (regla R15: tablero excluye `entregado`/`cancelado`,
  cierre autom�tico `entregado` ? `terminado`, reversi�n ? `pendiente`, regla unidireccional) y
  `docs/PLAN-IMPLEMENTACION.md` (estado del m�dulo Trabajo) y los contadores de `README.md` - verificar
  con `git grep` de los textos nuevos y que `docs/CASOS_DE_USO.md` queda sin modificar.
- [x] 4.2 Correr la verificaci�n de regresi�n del frontend: `npm test; npx tsc --noEmit; npm run lint;
  npm run build; npx playwright test` - verificar con 0 fallos y el E2E existente (10/10) a�n verde.
  Resultado: Vitest `54/54`, tsc/lint/build sin errores y Playwright `10/10` (sin c�digo de frontend nuevo).

## Workflow follow-up

- Validar con `openspec validate work-board-close-on-delivery --strict` y archivar con `/opsx-archive`
  una vez cumplidos los requisitos, para que los requirements aterricen en
  `openspec/specs/work-board/spec.md`.
- Commitear el change cuando el usuario lo autorice.