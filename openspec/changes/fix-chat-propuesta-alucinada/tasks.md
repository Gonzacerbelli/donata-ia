# Tasks

## 1. Guardrails: detección de escritura por raíz

- [x] 1.1 Agregar en `backend/tests/test_guardrails.py` los casos que fallan: `mentions_write_action("repone tapiz mural sol por 68 unidades manteniendo el precio")` es `True`; también `"reponé 5 unidades"`, `"agregá un cliente"`, `"cargá una venta"`, `"registrá un pago"`, `"cancelá la orden"`, `"actualizá el precio"`; y siguen en `False` las consultas `"qué productos debo reponer"`, `"cuánto resta por pagar"`, `"el pedido que resta cancelar"`.
- [x] 1.2 Implementar en `backend/app/services/llm/guardrails.py` la detección por raíz normalizada (tildes) con prefijo de token, conservando `QUERY_OVERRIDES`; verificar con `python -m pytest tests/test_guardrails.py -q` en verde.
- [x] 1.3 Agregar/ajustar en `backend/tests/test_guardrails.py` un test que confirme que consultas con `AMBIGUOUS_WRITE_VERBS` y `QUERY_OVERRIDES` no se marcan como escritura; verificar verde.

## 2. Agent: confirmación y afirmaciones de ejecución

- [x] 2.1 Agregar en `backend/tests/test_assistant.py` los casos que fallan: `agent._asks_confirmation("Vamos a reponer 68 unidades… ¿Confirmás esta acción?")` es `True`; también `"Confirmá en la pantalla"`, `"¿Me confirmás?"`, `"confirmalo"`; y `agent._claims_execution("Reponer stock: sumar 68 unidades. Hecho. Revisá el resultado en la pantalla.")` es `True`.
- [x] 2.2 Implementar en `backend/app/services/llm/agent.py`: normalizar tildes en `_CONFIRM_IN_UI`/`_asks_confirmation` cubriendo voseo (`confirmás`, `confirmá`) y agregar `_claims_execution`; verificar con `python -m pytest tests/test_assistant.py -q -k "confirmation or execution"` en verde.
- [x] 2.3 En el bloque sin tool calls de `run_agent` (~línea 426), forzar el registro de la propuesta (con reintento) cuando no hay propuesta y el texto pide confirmación **o** afirma ejecución, y sanear el texto quitando esas oraciones; verificar con un test unitario de `_without_confirmation`/guard.
- [x] 2.4 Agregar el fallback final: si el mensaje implica escritura (`mentions_write_action`) y no hay propuesta tras `MAX_STEPS`, devolver un mensaje seguro que no afirma éxito; verificar con un test unitario. (Cubierto por el saneo `deceptive` en el retorno y por el mensaje seguro de `MAX_STEPS`.)
- [x] 2.5 Agregar en `backend/tests/test_assistant.py` la regresión de `run_agent` con `_fake_agent_env`: el FakeLLM emite el texto alucinado exacto (`"Vamos a reponer 68 unidades… ¿Confirmás esta acción?\n\nReponer stock: sumar 68 unidades… Hecho. Revisá el resultado en la pantalla."`) para `"repone tapiz mural sol por 68 unidades manteniendo el precio"`; verificar que la respuesta final **no** afirma ejecución y `_has_proposal(log)` es `False` (o que el nudge registra la propuesta en la 2ª ronda); verde.
- [x] 2.6 Endurecer el camino de "llamada escrita como texto": si `_text_call_entry` devuelve una propuesta inválida (p. ej. id inexistente, detectado por `reference_feedback`), devolverle el error al modelo para que reintente con el id real (en vez de volcar el texto crudo), y nunca exponer al usuario el bloque `proponer_accion(...)`/`tool(...)` (helper `_strip_text_calls` aplicado antes del retorno final). Regresión: `test_run_agent_retries_text_call_with_bad_reference`, `test_run_agent_never_returns_raw_text_call`, `test_strip_text_calls_removes_call_block`.

## 3. Scope B: reducir la imitación del texto de confirmación

- [x] 3.1 Cambiar en `backend/app/services/llm/assistant.py` (`confirm_pending`) la frase `"… Hecho. Revisá el resultado en la pantalla."` por un formato claramente de resultado (`"Listo, quedó hecho: {resumen}."`).
- [x] 3.2 Actualizar `backend/tests/test_assistant.py::test_chat_write_requires_ui_confirmation` (assert de `startswith`) al nuevo texto y verificar `python -m pytest tests/test_assistant.py -q` verde.

## 4. Verificación integral

- [x] 4.1 Correr `ruff format app tests scripts; ruff check app tests scripts` (limpio) y `pytest` (249/249 verde). Por la latencia de Atlas remoto (~11–15 s por test por el fixture `db`), la suite completa se verificó **por archivo** en vez de una sola corrida: `test_assistant`+`test_guardrails` (139), `test_auth` (15), `test_catalog` (8), `test_sales` (12), `test_reports` (3), `test_users` (2), `test_security` (9), `test_chat_history`+`test_notifications` (15), `test_mcp_server` (10), `test_vector_store` (4), `test_exports` (9), `test_work_items` (23) = 249 verdes.
- [x] 4.2 Prueba manual: reiniciar la API y enviar por el chat `"repone tapiz mural sol por 68 unidades manteniendo el precio"`; verificar que aparece el botón de confirmación, que el stock del "Tapiz mural Sol" pasa de 0 a 68 sólo tras confirmar y que la respuesta no afirma "Hecho" antes de confirmar. **Verificado por el usuario.**
- [x] 4.3 Endurecer la resolución de referencias del agente: el modelo 14B a veces **inventa** los ObjectId y no llama a `buscar_productos`, repitiendo la misma propuesta inválida hasta agotar `MAX_STEPS` (3–5 min sin resultado). Se agregó resolución **por nombre** determinística (`_match_by_name`, `resolve_invalid_references`, `resolve_entry_references`) aplicada a los tres caminos (texto, tool nativa de escritura y tool nativa `proponer_accion`), que corrige el id usando el nombre del producto/cliente presente en el mensaje; más un corte temprano `MAX_IDENTICAL_FAILURES=2` para no colgar en propuestas repetidas. Regresiones: `test_match_by_name_picks_the_product_named_in_the_text`, `test_match_by_name_ignores_ambiguous_text`, `test_run_agent_resolves_hallucinated_product_id_by_name`, `test_run_agent_stops_after_repeated_identical_failures`. E2E real con Ollama: 63,5 s, `pending_action` con el id correcto `6aca6dc2bd6d325d5f281657`.

## Workflow follow-up

- Sincronizar el delta a `openspec/specs/ai-chat-assistant/spec.md` (`openspec sync`/archive) recién cuando el usuario confirme que la prueba manual pasó.
- Actualizar `docs/PLAN-IMPLEMENTACION.md` con la nota de corrección al archivar.
