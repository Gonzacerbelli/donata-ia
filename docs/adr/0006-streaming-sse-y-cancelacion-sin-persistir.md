# 0006. Streaming SSE sin librería y turno cancelado sin persistir

**Estado:** Aceptada
**Fecha:** 20261008
**Contexto:** El chat se servía con `POST /chat` (request/response): el frontend sólo podía
mostrar un estado de "pensando" hasta que llegaba la respuesta íntegra, y en respuestas largas
(consultas con varias herramientas) la espera se hacía perceptible. Se pidió cerrar el desvío
7.3 del plan: respuesta token a token sin perder el contrato existente, el rate limit ni la
garantía de que un turno interrumpido no deje estado a medias.

## Alternativas consideradas

1. **`sse-starlette` (o similar)** — helper `EventSourceResponse` con keep-alive y reconexión
   - A favor: menos código propio y manejo de heartbeat resuelto.
   - En contra: dependencia nueva en el backend, y el caso de uso es un único turno por
     conexión (el cliente no se reconecta a un stream compartido), donde el helper aporta poco.
2. **WebSockets** — duplex sobre la misma conexión.
   - A favor: reconexión y canales servidor→cliente en ambos sentidos.
   - En contra: exige handshake propio, otro origen para CORS/CSRF, y el chat es
     request→stream→fin; el cliente no vuelve a hablar por esa conexión.
3. **SSE manual con `StreamingResponse`** — un generador async que escribe frames
   `event:`/`data:` y cierra al terminar.
   - A favor: cero dependencias, el contrato de eventos queda explícito en el código, y
     `POST /chat` sigue intacto como fallback.
   - En contra: hay que escribir (y testear) el parser de frames del lado del cliente.

## Decisión

SSE manual, con dos reglas atadas al contrato:

- **Eventos por turno:** `start`, `token`, `tool_start`, `tool_end`, `pending_action`,
  `done`, `error`. `done` es la única verdad final: trae la respuesta **ya saneada** por los
  guardrails, que puede diferir del texto parcial acumulado, y el cliente lo usa para
  reemplazar lo mostrado. `POST /chat` queda sin cambios como fallback no-streaming.
- **Cancelación sin persistencia:** si el cliente se desconecta antes de `done` (cerrar el
  panel, recargar, `AbortController`), el backend cancela la tarea del agente y **no persiste
  nada de ese turno** — ni el mensaje del usuario ni la respuesta parcial. La persistencia
  ocurre recién después de que `run_agent` termina. Un turno a medias en el historial es peor
  que un turno inexistente: el usuario puede reenviarlo.
- Rate limit: `path == "/chat/stream"` comparte la ventana `chat` (20/min) con `POST /chat`
  y se deduce **antes** de abrir el stream, para no consumir tokens de modelo en un 429.

## Consecuencias

**A favor:** cero dependencias nuevas; el contrato de eventos es un spec versionado en
`openspec/specs/ai-chat-assistant/spec.md`; el modo de cancelación es testeable
(`test_chat_stream_*` y el E2E de historial espera el cierre del stream).

**En contra:** sin keep-alive propio, un proxies intermedio podría cortar streams largos
(aceptado: los turnos son < `OLLAMA_TIMEOUT=60s`); el cliente que recarga a mitad de turno
pierde ese turno por diseño (hay que explicarlo, no es un bug).

**Impacto en el código:** `backend/app/routers/chat.py` (`_sse`, `POST /chat/stream`),
`backend/app/services/llm/assistant.py` (`stream_message`),
`backend/app/services/llm/agent.py` (`run_agent(emit=...)`),
`backend/app/middleware/security.py`, `frontend/src/features/chat/sse.ts`,
`frontend/src/features/chat/api.ts` (`chatApi.stream`),
`frontend/src/features/chat/components/ChatWidget.tsx`.
