# Design

## Context

`POST /chat` ejecuta `assistant.handle_message` con un solo `await` y devuelve
`{thread_id, response, tool_calls, pending_action}` al final (ver proposal.md — Why). El agente
(`run_agent`) es un bucle manual de hasta 8 pasos sobre `ChatOllama.ainvoke` con tools MCP por
stdio; sólo el texto de la última vuelta es la respuesta del usuario. Los guardrails
(`sanitize_answer`/`validate_answer`) y la persistencia del turno ocurren **después** de tener el
texto completo. No hay `StreamingResponse`, `astream` ni SSE en el repo; `sse-starlette` no está
instalado. El rate limit resuelve `/chat` por path exacto (20 req/min).

## Goals / Non-Goals

**Goals:**

- Texto incremental del asistente en pantalla durante el turno.
- Visibilidad de la actividad de tools (el widget ya pinta chips de `tool_calls`).
- Contrato de streaming versionado en eventos, con `done` como verdad final.
- Cero regressión del flujo request/response existente (E2E y scripts).

**Non-Goals:**

- No se reemplaza `POST /chat` ni se rompe su contrato.
- No se persisten eventos parciales ni se reanuda un stream interrumpido (`Last-Event-ID` fuera de alcance).
- No se cambia el bucle de tool-calling, los guardrails ni el modelo de pending actions.
- No se agrega ninguna dependencia nueva.

## Decisions

1. **Endpoint nuevo `POST /chat/stream` en lugar de transformar `POST /chat`.**
   Alternativa: cambiar `POST /chat` a SSE (rompe clientes que esperan JSON: E2E de Playwright,
   `scripts/e2e_check.py`, el propio frontend como fallback). El endpoint nuevo mantiene ambos
   mundos con un costo mínimo de duplicación en el router.

2. **SSE con `StreamingResponse(media_type="text/event-stream")` sin `sse-starlette`.**
   El protocolo es `event:` + `data: <json>` + `\n\n`; el keep-alive no hace falta (el primer
   evento sale en el mismo request) y evitar la dependencia nueva es regla del repo.

3. **Un solo camino de código en el agente: `run_agent(..., emit=None)`.**
   `emit` es un callback `async (event: str, payload: dict) -> None` sin default (no-op). Con
   `emit=None` el comportamiento es byte a byte el actual; con callback se envían los eventos.
   Alternativa descartada: un `run_agent_stream` generador — duplicaría el bucle de 8 pasos y el
   manejo de nudge/propuestas.

4. **Tokens: `llm.astream` en todas las vueltas, filtrando chunks de tool calls.**
   Se emite sólo `content` textual, nunca los argumentos de tool calls (eso iría en
   `tool_start`). No es posible saber de antemano si una vuelta es la final; en la práctica qwen
   sólo genera prosa en la vuelta final, y el evento `done` lleva la respuesta final saneada que
   **reemplaza** el texto acumulado en cliente (así lo exige el spec: "Guardrails reescriben la
   respuesta"). Los eventos `token` de vueltas intermedias, si los hubiera, quedan absorbidos por
   `done`.
   Riesgo de nudge: el texto intermedio que alimenta la vuelta del nudge se emite y luego es
   reemplazado por `done` — comportamiento aceptado y cubierto por el mismo requisito.

5. **Errores post-apertura como evento `error`.** Una vez enviado el status 200 del stream no
   hay forma de responder 503/422 por HTTP: `handle_message` ya envuelve todo en
   `DependencyUnavailableError`; el handler del stream la traduce a
   `event: error` / `data: {"detail": "<mensaje en español>"}` — mismo contrato de `detail` que
   consume `ApiError` en `lib/http.ts`. Antes de abrir el stream (401 de auth, 429 de rate limit)
   se responde por HTTP normal.

6. **Cancelación natural = no persistir.** La persistencia ocurre dentro de `handle_message`,
   sólo al final del turno; si el cliente se desconecta, `StreamingResponse` cancela el generador
   y `asyncio.CancelledError` llega antes del append → el turno interrumpido no se persiste,
   tal como pide el spec. Se envuelve el generador en `try/except asyncio.CancelledError` para
   cerrar sin errores ruidosos en logs.

7. **Rate limit: rama explícita `path == "/chat/stream"` → ventana `chat`.** No se usa
   `startswith("/chat")` porque atraparía `/chat/threads` y `/chat/confirm`, que hoy están en la
   ventana `write` (60/min) — cambiar eso sería un efecto colateral no pedido.

8. **Frontend: `fetch` + `response.body.getReader()` con Bearer.** `EventSource` no envía
   header `Authorization` (el chat exige JWT). Parser propio y pequeño (separar por `\n\n`,
   manejar chunks partidos entre lecturas) en una función pura y testeable. Estado
   `streamingText` local en el widget; en `done` se reemplaza el mensaje, se setea
   `pendingAction` y se invalida `chatKeys.messages(threadId)` para que el historial del servidor
   (con ids reales) reemplace lo local. `AbortController` al cerrar el widget o cambiar de hilo.

## Risks / Trade-offs

- [Middlewares `BaseHTTPMiddleware` (CORS, rate limit) podían bufferingar el stream] → verificar
  con una corrida real que los `token` llegan incrementalmente (no al final); si bufferiza, mover
  la comprobación a los tests E2E y revisar el orden de middlewares.
- [Texto intermedio de vueltas no finales emitido como `token`] → `done` reemplaza siempre el
  acumulado; filtrado de chunks de tool calls.
- [Rate limit de 20 turnos/min corta pruebas manuales] → los tests lo desactivan
  (`conftest.py`) y en dev se respeta el `Retry-After` de la UI.
- [Contrato SSE frágil si el parser del frontend falla con chunks partidos] → función pura de
  parsing con tests unitarios de casos partidos (`"da` + `ta: ...\n\n"`).

## Migration Plan

Aditivo: sin cambios de datos ni de deploy. Rollback = revertir el commit (el endpoint nuevo no
es usado por nadie si se quita).

## Open Questions

<!-- ninguna: las decisiones de arriba cubren alcance, comportamiento y verificación -->
