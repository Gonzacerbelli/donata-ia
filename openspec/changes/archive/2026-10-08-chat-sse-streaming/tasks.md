# Tasks

## 1. Backend — agente con emisión de eventos

- [x] 1.1 Agregar el parámetro `emit` (callback async opcional, no-op por defecto) a `run_agent` y emitir `tool_start`/`tool_end` en cada herramienta (lectura y propuesta de escritura) — verificable con un test en `backend/tests/test_assistant.py` que captura los eventos emitidos y otro que con `emit=None` el retorno es idéntico al actual.
- [x] 1.2 Cambiar la invocación del LLM de `ainvoke` a `astream` filtrando chunks de tool calls, emitiendo `token` con el contenido textual de cada vuelta — verificable con un test que usa un LLM falso que produce chunks y aserta que se reciben eventos `token` en orden y que el texto final retornado es el mismo de antes.

## 2. Backend — endpoint SSE

- [x] 2.1 Crear `POST /chat/stream` en `backend/app/routers/chat.py` con `StreamingResponse` (`text/event-stream`) que emite `start`, `token`, `tool_start`, `tool_end`, `pending_action`, `done` y `error`, con persistencia del turno igual a la actual y `try/except asyncio.CancelledError` — verificable con un test de integración con `auth_client` + `monkeypatch` de `run_agent` que parsea el stream y aserta el orden de eventos, el `done` con la respuesta final y la persistencia en el historial del hilo.
- [x] 2.2 Manejar errores: 401 sin JWT (sin abrir el stream) y fallo del turno post-apertura como evento `error` con `{"detail": ...}` en español — verificable agregando el caso 401 a `test_chat_routes_require_auth` en `backend/tests/test_chat_history.py` y un test del evento `error` con el agente lanzando `DependencyUnavailableError`.
- [x] 2.3 Agregar la rama `path == "/chat/stream"` a `_resolve_limit` en `backend/app/middleware/security.py` para que use la ventana `chat` (20/min) — verificable con un test en `backend/tests/test_security.py` (429 + `Retry-After` con rate limit activo) que confirme que `/chat/threads` y `/chat/confirm` siguen en la ventana `write`.

## 3. Frontend — transporte y UI de streaming

- [x] 3.1 Crear una función pura de parsing SSE (separación por `\n\n`, manejo de chunks partidos entre lecturas) en `frontend/src/features/chat/` — verificable con tests unitarios en Vitest que cubren un frame completo, un frame partido en dos lecturas y frames múltiples en un mismo chunk (`npm test`).
- [x] 3.2 Agregar `chatApi.stream()` con `fetch` + `response.body.getReader()` + header `Authorization` + `AbortController`, y los tipos de evento del stream en `frontend/src/types/domain.ts` — verificable con `npx tsc --noEmit` y un test unitario con `fetch` mockeado que consume el reader y devuelve los eventos parseados.
- [x] 3.3 Integrar el streaming en `ChatWidget.tsx`: texto parcial incremental durante el turno, reemplazo por el `done`, `pendingAction` desde el `done`, invalidación de `chatKeys.messages(threadId)` al terminar y abort al cerrar el widget o cambiar de hilo — verificable con `npx tsc --noEmit`, `npm run lint` y una prueba manual contra el backend con Ollama corriendo viendo los tokens aparecer incrementalmente.

## 4. Integración y documentación

- [x] 4.1 Actualizar `docs/PLAN-IMPLEMENTACION.md` §7.3 para marcar el streaming SSE como implementado (una vez verde el cambio) — verificable con `grep -n "SSE" docs/PLAN-IMPLEMENTACION.md` mostrando el estado nuevo y sin tocar `docs/CASOS_DE_USO.md`.
- [x] 4.2 Correr la verificación completa del backend (`ruff format`, `ruff check`, `pytest`) — verificable con `pytest_exit=0` en la salida.
- [x] 4.3 Correr la verificación completa del frontend (`npm test`, `npx tsc --noEmit`, `npm run lint`, `npm run build`) — verificable con 0 fallos en cada comando.
- [x] 4.4 Verificar el flujo end-to-end real con Ollama: `POST /chat/stream` con un mensaje de negocio devuelve `start` + `token` incrementalmente + `done` con `pending_action` cuando corresponde, y el E2E de Playwright existente sigue en verde (9/9).

## Workflow follow-up

- Archivar el change con `/opsx-archive` para que los requirements de streaming aterricen en `openspec/specs/ai-chat-assistant/spec.md`.
- Commitear la implementación cuando el usuario lo autorice.
