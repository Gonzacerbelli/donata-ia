# Design

## Context

El flujo del turno vive en `app/services/llm/agent.run_agent` (`backend/app/services/llm/agent.py`).
En el bucle de hasta `MAX_STEPS` (8) pasos, cuando el modelo responde **sin tool calls** hay una
serie de guards que deciden qué texto se devuelve (líneas ~390-443). Hoy:

- `_CONFIRM_IN_UI` (`agent.py:147`) detecta pedidos de confirmación pero **no** reconoce el voseo
  con tilde: "Confirmás" no matchea (`ma|me|…` con `\b` sobre "má").
- `guardrails.mentions_write_action` (`guardrails.py:284`) reconoce sólo infinitivos/imperativos
  limitados; el usuario escribió **"repone"** (conjugado), que no matchea `reponer`.

Con ambos guards apagados, un texto que imita el formato de confirmación del historial
(`assistant.confirm_pending` en `assistant.py:249` produce "… Hecho. Revisá el resultado en la
pantalla.") pasa tal cual y `run_agent` retorna `tool_calls = []`. `assistant._pending_from`
no encuentra `proponer_accion` y deja `pending_action = null`: no hay botón y nada se ejecuta.

Ver también `proposal.md` (Why) y `specs/ai-chat-assistant/spec.md` (requisitos).

## Goals / Non-Goals

**Goals:**

- Garantizar de forma determinística que la respuesta nunca afirme una escritura ni pida confirmar
  cuando no hay una propuesta registrada.
- Reconocer confirmaciones y pedidos de escritura en voseo/formas conjugadas y con/sin tildes.
- Reducir la imitación few-shot del texto de confirmación ejecutada.

**Non-Goals:**

- No se cambia el contrato de la API ni el esquema de `pending_action`.
- No se persiste el botón de confirmación entre recargas (deuda aparte).
- No se toca `docs/CASOS_DE_USO.md`.
- No se cambia de modelo ni se agregan dependencias.

## Decisions

### 1. Detección de escritura por raíz, con normalización de tildes

`guardrails.mentions_write_action` pasará a normalizar tildes (`_normalize` ya existe) y a matchear
**prefijos de token** con una lista de raíces: `repon`, `reposic`, `agreg`, `carg`, `registr`,
`crea`/`crear`, `modific`, `actualiz`, `edit`, `cancel`, `pag`, `elimin`, `borr`, `ingres`, `sumar`.
Se mantiene la lógica de `QUERY_OVERRIDES` para que consultas ("qué debo reponer", "por pagar") no
cuenten como acción.

- **Por qué prefijo de token y no substring**: evita falsos positivos ("pag" dentro de "pago" como
  sustantivo de cobranza se acota con `QUERY_OVERRIDES`); el patrón de tokens ya se usa en
  `mentions_read_action`.
- **Alternativa descartada**: lista exhaustiva de conjugaciones (frágil, se desactualiza).

### 2. Confirmación tolerante a tildes y conjugaciones

`_CONFIRM_IN_UI` normalizará el texto (tildes → sin tildes) antes de matchear, y cubrirá:
`confirm` seguido de `a|as|á|ás|o|ame|alo|ala|e|en|emos|ar` como raíz, o el patrón existente de
"requiere/necesita/pide/pendiente de confirmación". Se mantiene `_asks_confirmation` y
`_without_confirmation` sin cambios de firma.

### 3. Detección de afirmaciones de ejecución

Nuevo `_claims_execution(text)` en `agent.py`: reconoce "hecho", "listo", "ejecutado/a",
"realizado/a", "revisá el resultado", "se actualizó", "se repuso" y el emoji "✅". Se usa sólo en el
bloque sin tool calls.

### 4. Guard y fallback en el bloque sin tool calls

En `agent.py` (~línea 426), si `not _has_proposal(tool_calls_log)` y (`_asks_confirmation(text)` **o**
`_claims_execution(text)`): pedir reintento con `NO_PROPOSAL_FEEDBACK` (una vez) y, agotado el
reintento, **sanear el texto** quitando las oraciones que piden confirmación o afirman ejecución. Si
tras el bucle persiste un pedido de escritura (`mentions_write_action(message)`) sin propuesta, el
retorno final será un **mensaje seguro** ("No pude registrar la acción para que la confirmes. ¿Querés
reformularla?") en lugar del texto del modelo.

- **Por qué determinístico en el servidor y no sólo en el prompt**: el modelo local ya ignora la
  instrucción del prompt en algunos turnos; la garantía debe ser del código.
- **Alternativa descartada**: confiar sólo en `PROPOSE_NUDGE`/prompt (es justamente lo que falló).

### 5. Reformular el texto de confirmación ejecutada (Scope B)

`assistant.confirm_pending` (`assistant.py:249`) pasará de `f"{summary}. Hecho. Revisá el resultado
en la pantalla."` a un formato claramente de resultado, por ejemplo
`f"Listo, quedó hecho: {summary}."` / un prefijo visible de resultado, para que el modelo no lo
reutilice como plantilla de propuesta.

- **Por qué**: el turno confirmado es la única fuente de esa frase; al cambiarla y marcarla como
  resultado, se reduce la contaminación few-shot.
- **Breaking**: cambia texto de UI y un assert de test (`test_assistant.py:586`), sin afectar API.

### 6. Resolución de referencias por nombre (endurecimiento del tool-calling)

Durante la verificación manual se observó que el modelo 14B **inventa los ObjectId** de producto: en
un turno no llamó a `buscar_productos` y propuso 8 veces el mismo id inexistente
(`6aca6dc4bd6d325d5f28165e`), agotando `MAX_STEPS` en 3–5 min sin resultado. Para no depender de que
el modelo copie un ObjectId de 24 caracteres:

- Nuevo `resolve_invalid_references(db, args, hint)` + `_match_by_name`: si un `producto_id`/
  `cliente_id`/`product_id` (de `items`) no existe, se busca la entidad cuyo nombre aparezca en el
  texto del usuario (y en el `resumen`) y se corrige el id. Es determinístico y sólo actúa cuando hay
  un único nombre coincidente; si es ambiguo, no adivina.
- Se aplica en los tres caminos que podían registrar una propuesta: llamada escrita como texto,
  tool nativa de escritura (`WRITE_TOOLS`) y tool nativa `proponer_accion`.
- Corte temprano `MAX_IDENTICAL_FAILURES = 2`: si la misma propuesta inválida se repite, se devuelve
  `UNRESOLVED_REFERENCE_REPLY` (mensaje seguro, sin afirmar éxito) en vez de iterar hasta `MAX_STEPS`.

- **Por qué server-side**: los ids son un detalle interno; exigirle al modelo copiarlos es frágil. La
  resolución por nombre usa la misma fuente de verdad (los repositorios) que el resto del negocio.
- **Alternativa descartada**: bajar `MAX_STEPS` (sólo acelera el fallo, no resuelve el caso correcto).

## Risks / Trade-offs

- [Falsos positivos de `mentions_write_action` por raíces amplias] → se conserva `QUERY_OVERRIDES` y
  se agregan tests con consultas reales del dominio.
- [Sobre-bloqueo en consultas legítimas] → el guard sólo actúa cuando el texto pide confirmación o
  afirma ejecución, no en cualquier texto.
- [El modelo reintenta y vuelve a alucinar] → el fallback final devuelve el mensaje seguro; nunca se
  afirma éxito sin propuesta.
- [Cambio de frase del confirm rompe un test existente] → se actualiza en la misma tarea del Scope B.
- [Resolución por nombre con un match erróneo] → sólo se corrige cuando el nombre coincide de forma
  única (y no ambigua); ante duda no se toca el id y se cae al corte temprano con mensaje seguro.

## Verificación de invariantes de negocio

- **Escrituras sólo con confirmación humana**: el guard no ejecuta nada; sólo fuerza el registro de
  la propuesta por `proponer_accion` y el ejecutor sigue siendo `POST /chat/confirm`.
- **Montos enteros y saldos derivados**: sin cambios; el saneado (`sanitize_answer`) sigue aplicándose.
- **Stock atómico**: sin cambios; la reposición real ocurre recién en el confirm, como hoy.
