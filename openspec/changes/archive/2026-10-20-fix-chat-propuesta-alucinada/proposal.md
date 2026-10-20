# Proposal

## Why

En el CU07 (`docs/CASOS_DE_USO.md`), cuando el usuario pide una escritura, el modelo local puede
devolver un texto que **finge** una propuesta y una ejecución ("Hecho. Revisá el resultado en la
pantalla.") **sin emitir ninguna tool call**, imitando el turno anterior del historial. El
resultado es que no se registra `pending_action` (no aparece el botón de confirmación) y **nada se
ejecuta**, violando el requisito "Toda escritura desde el chat exige confirmación humana": el
usuario cree que la acción se hizo y el negocio no cambió.

Evidencia observada en la base: turno de `reponer_stock` del "Tapiz mural Sol" con `tool_calls: []`,
el producto en `stock = 0` y sin ningún `stock_moves` de reposición. Las dos redes de seguridad que
debían atraparlo no se dispararon: la detección de confirmación no reconoce el voseo con tilde
("Confirmás") y la detección de intención de escritura sólo reconoce infinitivos ("reponer"), no
formas conjugadas como "repone".

## What Changes

- **Nunca afirmar éxito sin propuesta**: si un turno termina sin una propuesta registrada y el texto
  pide confirmación o afirma una ejecución ("Hecho", "Listo", "Ejecutado", "Revisá el resultado…"),
  el sistema **no** SHALL devolver ese texto. Fuerza el registro de la propuesta (reintento) y, si
  aún así no lo logra, responde un mensaje seguro sin afirmar éxito y con `pending_action = null`.
- **Detección de confirmación tolerante a tildes y conjugaciones**: reconocer "confirmá", "confirmás",
  "confirmas", "confirmame", "confirmalo", "confirmala", "confirme", etc.
- **Detección de intención de escritura por raíz**: reconocer formas conjugadas y voseo ("repone",
  "reponé", "agregá", "creá", "registrá", "pagá", "cancelá", "modificá", "actualizá", "eliminá",
  "borrá") además de los infinitivos actuales, sin marcar consultas ("qué debo reponer", "por pagar").
- **Menos imitación few-shot**: reformular la respuesta de confirmación ejecutada
  (`assistant.confirm_pending`) a un formato claramente de resultado, para reducir que el modelo la
  copie como plantilla de propuesta. **BREAKING** sólo a nivel de texto de UI: cambia la frase
  "… Hecho. Revisá el resultado en la pantalla.".
- Sin cambios de contrato de API, sin dependencias nuevas, sin cambios en `docs/CASOS_DE_USO.md`.

## Capabilities

### New Capabilities

<!-- ninguna -->

### Modified Capabilities

- `ai-chat-assistant`: se modifica el requisito "Toda escritura desde el chat exige confirmación
  humana" (la respuesta nunca afirma ejecución sin propuesta registrada) y se agrega un requisito
  sobre no simular propuestas ni ejecuciones.

## Impact

- **Backend:** `app/services/llm/guardrails.py` (`mentions_write_action` por raíz),
  `app/services/llm/agent.py` (`_CONFIRM_IN_UI`/`_asks_confirmation` tolerantes a tildes,
  nuevo `_claims_execution`, guard del bloque sin tool calls y fallback),
  `app/services/llm/assistant.py` (texto de la respuesta de confirmación).
- **Tests:** `backend/tests/test_guardrails.py` y `backend/tests/test_assistant.py`
  (unitarios de detección + regresión de `run_agent` con el texto alucinado).
- **Frontend:** sin cambios (el botón ya se renderiza iff `pending_action` no es nulo).
- **Docs:** `docs/PLAN-IMPLEMENTACION.md` (nota de corrección en F6/F7 al archivar);
  `docs/CASOS_DE_USO.md` **no se toca** (entregable validado).
