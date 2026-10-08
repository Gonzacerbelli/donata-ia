# Proposal

## Why

El CU07 define streaming SSE para el chat y hoy `POST /chat` es request/response: el usuario ve
"Pensando…" durante toda la latencia del bucle de tools MCP (hasta 8 pasos, proceso stdio y RAG)
y recién ve texto cuando todo terminó. Es el único pendiente documentado de F7
(`docs/PLAN-IMPLEMENTACION.md` §7.3) y vale 2 puntos de rúbrica.

## What Changes

- Nuevo endpoint `POST /chat/stream` que responde `text/event-stream` con eventos `start`,
  `token`, `tool_start`, `tool_end`, `pending_action`, `done` y `error`.
- `POST /chat` (request/response) **se mantiene** como fallback: no es un cambio *BREAKING*;
  lo siguen usando los scripts E2E y los clientes que no consumen streaming.
- El agente (`run_agent`) gana una variante con streaming de tokens en la vuelta final
  (`ChatOllama.astream`) emitiendo eventos por callback, sin cambiar el contrato existente.
- El guardrails se mantiene: el evento `done` emite la respuesta final saneada y reemplaza el
  texto parcial acumulado en cliente (los sanitizados de `assistant` pueden reescribir el texto).
- Frontend: transporte con `fetch` + reader y header `Authorization` (EventSource no manda Bearer),
  mensaje assistant parcial en pantalla durante el stream, reemplazo en `done` e
  invalidación del historial del hilo.
- Rate limit: `/chat/stream` queda en la ventana `chat` (20 req/min), igual que `/chat`.
- Sin dependencias nuevas: se usa `StreamingResponse` de FastAPI/Starlette (ya instalado).

## Capabilities

### New Capabilities

<!-- ninguna -->

### Modified Capabilities

- `ai-chat-assistant`: se agregan requisitos de comportamiento observable de streaming
  (eventos del stream, texto incremental en el cliente, fallback, errores post-apertura y
  rate limit del stream) que hoy la spec as-built marca como `<!-- Pendiente: streaming SSE -->`.

## Impact

- **Backend:** `app/routers/chat.py` (nuevo endpoint), `app/services/llm/agent.py` (variante
  con `astream` + emisión de eventos), `app/services/llm/assistant.py` (orquestación del
  stream y eventos), `app/schemas/chat.py` (eventos), `app/middleware/security.py`
  (`_resolve_limit` para `/chat/stream`).
- **Frontend:** `src/features/chat/api.ts` (transporte fetch+reader), `src/features/chat/ChatWidget.tsx`
  (estado de streaming), `src/types/domain.ts` (tipos de evento), `src/features/chat/hooks.ts`
  (invalidación al `done`).
- **Tests:** `backend/tests/test_assistant.py` / `test_chat_history.py` / `test_security.py`;
  nuevos tests unitarios del parser de eventos en el frontend; E2E de Playwright existente
  debe seguir pasando contra `POST /chat`.
- **Docs:** `docs/PLAN-IMPLEMENTACION.md` §7.3 (pendiente SSE → resuelto al archivar);
  `docs/CASOS_DE_USO.md` **no se toca** (entregable validado).
