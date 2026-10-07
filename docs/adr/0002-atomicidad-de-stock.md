# 0002. Atomicidad de stock por update condicional

**Estado:** Aceptada
**Fecha:** 20261003
**Contexto:** Al crear una venta hay que descontar stock de varios productos. Si dos ventas
concurrentes piden el último ítem, no puede quedar stock negativo ni "stock fantasma".

## Alternativas consideradas

1. **Transacción de MongoDB** — `session.with_transaction`.
   - A favor: garantía fuerte y bien conocida.
   - En contra: **MongoDB standalone no soporta transacciones** (requiere replica set); el
     entorno de desarrollo corre standalone. Rechazada.
2. **Optimistic locking** — leer la versión, comparar y reintentar.
   - A favor: portable.
   - En contra: hay que exponer `version` en el modelo y escribir el reintento; más superficie.
3. **Update condicional atómico** — `find_one_and_update({"stock": {"$gte": qty}}, {"$inc": {...}})`.
   - A favor: una sola operación atómica del motor; sin `version`; portable en standalone.
   - En contra: si falla hay que **revertir manualmente** los ítems ya descontados.

## Decisión

Todo descuento de stock es un `find_one_and_update` condicional. La creación de venta procesa los
ítems y, si **cualquiera** falla, ejecuta un **rollback total** reingresando los ya descontados
(no parcial). Cada movimiento escribe su registro en `stock_moves` (cantidad con signo,
`stock_after`, motivo y referencia). Un movimiento nunca se borra: el "deshacer" genera uno
inverso.

## Consecuencias

**A favor:** correcto en standalone; simple de razonar; auditable.

**En contra:** el rollback es responsabilidad de la aplicación; hay que testear el caso de fallo
en el medio de la lista de ítems.

**Impacto en el código:** `backend/app/repositories/products.py` (`adjust_stock_atomic`),
`backend/app/services/sales.py`, `backend/app/services/stock.py`.