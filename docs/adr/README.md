# docs/adr/ — Architecture Decision Records

Registro de decisiones técnicas. Un ADR por decisión que **no sea obvia**.

## Cuándo escribir un ADR

Escribilo cuando una decisión cumple alguna de estas:

- Hay **más de una alternativa razonable** y elegiste una.
- La decisión tiene un **costo conocido** que aceptaste.
- Alguien va a preguntarse *"¿por qué está hecho así?"* en seis meses.
- La decisión viene de un **requisito del cliente**, no de preferencia técnica.

**No** escribas un ADR para lo obvio. "Usamos FastAPI porque es lo que pidió el TP" no lo
necesita. "Las tools del agente llaman a los services y no a los routers" sí, porque la
alternativa parece razonable y tiene consecuencias.

## Formato

Nombres: `0001-slug-corta-en-espanol.md`, numeración correlativa.

```markdown
# NNN. Título de la decisión

**Estado:** Aceptada | Reemplazada por NNNN | Obsoleta
**Fecha:** AAAAMMDD
**Contexto:** Qué problema o requisito obliga a decidir.

## Alternativas consideradas

1. Opción A — ventajas y contras
2. Opción B — ventajas y contras
3. Opción elegida

## Decisión

Qué se hace, con precisión.

## Consecuencias

**A favor:** qué se gana.
**En contra:** qué se pierde o qué costo se acepta.
**Impacto en el código:** qué archivos quedan atados a esta decisión.
```

## Decisiones ya tomadas (documentadas en `AGENTS.md` y `ARQUITECTURA.md`)

Estas no tienen ADR propio porque ya están explicadas en detalle allá. Si alguna vez se
cuestionan, se les escribe un ADR acá.

| # | Decisión | Dónde está explicada |
|---|---|---|
| 1 | Sin roles de usuario | `AGENTS.md` §3.1 |
| 2 | Producto siempre con proveedor | `AGENTS.md` §3.2 |
| 3 | IA 100 % local (Ollama 7B) | `AGENTS.md` §3.3 · skill `ollama-local` |
| 4 | El LLM sólo accede mediante tools tipadas | `ARQUITECTURA.md` §6.2 |
| 5 | Montos en enteros ARS | `AGENTS.md` §3.6 |
| 6 | Saldo siempre derivado | `AGENTS.md` §3.7 |
| 7 | Stock atómico con auditoría | `AGENTS.md` §3.9 |
| 8 | Spec-Driven Development | `AGENTS.md` §7 · ADR `0005` |

## ADRs escritos

| # | Decisión | Archivo |
|---|---|---|
| 0001 | Las tools del agente se exponen en un servidor MCP propio | `0001-tools-del-agente-por-mcp.md` |
| 0002 | Atomicidad de stock por `update` condicional (sin transacciones) | `0002-atomicidad-de-stock.md` |
| 0003 | Búsqueda vectorial local con colecciones separadas (manual / catálogo) | `0003-busqueda-vectorial-local.md` |
| 0004 | Token de sesión en `localStorage` con validación de expiración en cliente | `0004-token-de-sesion-en-localstorage.md` |
| 0005 | OpenSpec como flujo Spec-Driven (reemplaza el flujo propio `sdd-openspec`) | `0005-openspec-como-flujo-sdd.md` |
| 0006 | Streaming SSE sin librería y turno cancelado sin persistir | `0006-streaming-sse-y-cancelacion-sin-persistir.md` |

## Decisiones que van a necesitar ADR durante el desarrollo

| Decisión pendiente | Por qué va a necesitar ADR |
|---|---|
| Dónde vive el estado de las notificaciones (derivado vs persistido) | Afecta consistencia y complejidad |
| Modelo de 7B elegido | El comportamiento de tool-calling varía mucho entre modelos del mismo tamaño |
| Integración de la IA en el flujo de órdenes | Si el chat puede crear órdenes o sólo consultarlas es una decisión de producto |
