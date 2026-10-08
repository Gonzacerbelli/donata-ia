# AI Engineering — Bitácora del proceso

> **Este documento es un entregable evaluado (1 pt documentación + 3 pts esquema de trabajo).**
> No es un informe de resultados: es el registro de **cómo** se construyó el sistema con IA.
>
> **Regla de escritura:** se completa *mientras* se trabaja, no al final. Si recién estás
> escribiendo la entrada de hace dos semanas, no la estás escribiendo bien.

---

## Cómo usar este documento

Por cada tarea relevante, agregar una entrada con esta estructura:

```markdown
### [AAAAMMDD] Tarea <nombre> — <estado>

**Objetivo.** Qué se pidió.

**Contexto dado a la IA.** Qué archivos, reglas y criterios se le dieron al agente
(cuanto más preciso, mejor el resultado).

**Prompt (esencial).** El fragmento del prompt que define el problema.

**Iteración.** Qué devolvió la IA → qué se corrigió → cuántas vueltas.

**Resultado.** Qué quedó hecho, y qué verificación lo prueba.

**Lección.** Qué se aprende para la próxima.
```

---

## 1. Entorno de trabajo

| Aspecto | Configuración | Por qué |
|---|---|---|
| Herramienta principal | **opencode** como CLI de desarrollo asistido | Agentes, comandos, skills y MCP configurables por proyecto |
| Archivo de contexto | `AGENTS.md` en la raíz | Se carga automáticamente en cada sesión: las decisiones del proyecto persisten |
| Framing del trabajo | **Spec-Driven Development** con [OpenSpec](https://github.com/Fission-AI/OpenSpec) | La especificación precede al código; `openspec/specs/` queda como estado as-built y cada cambio pasa por propuesta aprobada |
| Orquestación | Subagentes especializados por dominio | Un agente que hace una sola cosa pega más que uno que hace todo |
| Protocolo | **MCP** para contexto externo | Ver `docs/MCP.md` |
| Revisión | Ciclo de **revisión adversarial** antes de dar por terminado | "Implementá X" seguido de "¿qué se rompe en X?" encuentra errores que la implementación inicial no ve |
| Verificación | Tests como criterio de terminado | Sin test verde, la tarea no está terminada |
| Eficiencia de tokens | Contexto mínimo viable por tarea | Mandar el archivo entero "por las dudas" degrada la calidad de la respuesta |

### 1.1 Reglas del contexto escritas para este proyecto

En `AGENTS.md` se consolidaron las reglas que gobiernan todo el desarrollo:

| Regla | Origen | Por qué importa |
|---|---|---|
| Sin roles de usuario | Decisión del cliente | Evita construir un módulo de autorización que nadie va a usar |
| Producto siempre con proveedor | Decisión del cliente | Sin proveedor no hay reposición posible |
| IA local, nunca cloud | Decisión del cliente | Los datos del negocio no salen de la máquina |
| El LLM sólo usa tools tipadas | Diseño propio | Un modelo con acceso libre a datos puede romper invariantes |
| Montos en ARS enteros | Dominio | Un `float` de pesos introduce errores de redondeo reales |
| Saldo siempre derivado | Dominio | Persistir un campo calculado garantiza que algún día esté desactualizado |
| Stock atómico y auditado | Dominio | El control de concurrencia mal hecho genera stock fantasma |
| Comment-free code | Preferencia | Legibilidad por estructura, no por comentarios |

> **Por qué importa para la nota:** la rúbrica pide "uso correcto de reglas de contexto para
> guiar el desarrollo de la lógica y patrones de diseño". Escribir esas reglas en un archivo
> que la IA carga en cada sesión **es** el mecanismo. La tabla de arriba documenta que hubo
> criterio, no que se copiaron convenciones.

---

## 2. Configuración de agentes (AI Engineering en la práctica)

| Agente | Rol | Por qué existe como agente separado |
|---|---|---|
| Skills `openspec-*` (`/opsx-*`) | Ciclo spec → código: explore, propose, apply, verify, sync, archive | El proceso vive en instrucciones versionadas, no en la memoria de la conversación |
| `backend-engineer` | Implementa en FastAPI con las convenciones del proyecto | Contexto acotado al dominio backend |
| `frontend-engineer` | Implementa en React con las convenciones del proyecto | Contexto acotado al dominio frontend |
| `ai-engineer` | Agente de LangChain, tools y prompts del chat | El chat es un subsistema particular: necesita un prompt y una evaluación propios |
| `reviewer` | Revisión adversarial: "¿qué se rompe acá?" | Un revisor sin contexto de implementación encuentra más que el autor |
| `security-auditor` | Verifica la lista de `docs/SEGURIDAD.md` | La seguridad se audita contra una lista, no de memoria |

**El patrón:** el agente principal **delega**, no hace todo. El agente especializado entra con
contexto mínimo y devuelve un resultado acotado. Esto es orquestación, que es lo que evalúa la
rúbrica.

---

## 3. Técnicas de prompting aplicadas

| Técnica | Dónde se aplica | Por qué funciona |
|---|---|---|
| **Contexto explícito** | Cada tarea declara CU, reglas aplicables y criterios de aceptación | La IA no adivina el dominio: se lo decís |
| **Restricciones negativas** | *"No agregar roles"*, *"no usar API cloud"*, *"no comentar el código"* | Previene las decisiones por defecto que la IA haría mal |
| **Ejemplos** | System prompt del chat, schemas | El modelo de 7B aprende la forma por imitación, no por descripción |
| **Estructuración** | System prompt en secciones (rol / contexto / reglas / formato / ejemplos) | Un prompt difuso produce comportamiento errático en modelos chicos |
| **Temperatura baja para datos** | `OLLAMA_TEMPERATURE = 0.1` | Los datos de negocio no admiten creativity |
| **TDD como prompt** | "Escribí primero el test que falla" | Ancla el comportamiento esperado antes de la implementación |
| **División en subtareas** | Un CU → varias tareas atómicas | Reduce la probabilidad de que una respuesta larga se desvíe |
| **Reformulación tras el fallo** | Iteración | Si dos intentos fallan, cambiar el prompt es más barato que insistir |

---

## 4. Loops de autocorrección

### 4.1 Loop de implementación (el principal)

```
1. Se escribe el test que falla          → la IA lo hace
2. Se corre pytest                       → el fallo es la evidencia
3. Se implementa hasta que pase          → la IA itera
4. Se corre la suite completa            → no romper lo que ya andaba
5. Commit sólo con la suite verde        → el estado del repo es siempre coherente
```

**Por qué importa:** un agente de IA con tests no verificados escribe plausible pero incorrecto.
El test es el judge.

### 4.2 Loop de revisión adversarial

```
1. La IA implementa
2. Se la pregunta a otro agente: "¿qué se rompe acá?"
3. Se corrigen los problemas encontrados
4. Se repite hasta que la revisión no encuentra nada relevante
```

Este loop encuentra clases de errores que la implementación inicial no va a ver sola:
condiciones de carrera, casos borde, validaciones faltantes, estados inconsistentes.

### 4.3 Loop de evaluación del chat IA

El chat es lo más difícil de verificar, porque la salida es texto libre. El loop:

```
1. Definir un conjunto de casos (set de preguntas de prueba)
2. Correrlos contra el modelo real y anotar el resultado
3. Analizar los fallos: ¿eligió mal la tool? ¿pidió los datos de más?
   ¿se inventó un ID? ¿se saltó la confirmación?
4. Ajustar el prompt o la descripción de la tool
5. Repetir hasta que la tasa de acierto sea aceptable
```

**Este loop es el más importante del TP.** Un modelo de 7B en CPU no va a acertar el 100% de
las veces; lo que se busca es que acierte en los flujos frecuentes y **que no haga nada
peligroso cuando se equivoca**. El set de casos de prueba queda como evidencia.

---

## 5. Registro de iteraciones

<!-- Agregar las entradas acá, de la más reciente a la más antigua. -->

### [20261008] Adopción de OpenSpec y streaming SSE del chat — completado

**Objetivo.** Dos cosas pendientes del plan: instalar un flujo Spec-Driven verificable en lugar
del flujo propio declarado pero nunca ejercitado, y cerrar el desvío 7.3 del chat (SSE).

**Contexto para el agente.** `AGENTS.md` §7–§8 (flujo spec-driven), el flujo depreciable
(`.opencode/skills/sdd-openspec`, comandos `/sdd-*`, `specs/` vacía) y el desvío 7.3 de
`docs/PLAN-IMPLEMENTACION.md`. Para el streaming, el contrato quedó en
`openspec/changes/chat-sse-streaming/design.md` antes de tocar código.

**Prompts clave.**
1. *"Instalá OpenSpec, documentá los 10 CU como specs as-built validados y deprecá el flujo
   propio; no toques `docs/CASOS_DE_USO.md`."*
2. *"Implementá `chat-sse-streaming` desde el change aprobado: eventos `start/token/tool_start/
   tool_end/pending_action/done/error`, `POST /chat` intacto como fallback y rate limit en la
   ventana `chat`."*
3. *"Validá todo contra el plan y reportá las divergencias."*

**Iteraciones y hallazgos.**
- El flujo propio tenía comandos declarados inexistentes (`/sdd-tasks`) y specs vacías desde el
  commit inicial: OpenSpec lo reemplazó con `validate`/`archive` y un backfill as-built de 10
  specs (103 requirements) validado en estricto.
- **Cancelación y persistencia:** con streaming, recargar o cerrar el panel corta el turno; la
  decisión de diseño es que un turno interrumpido **no se persiste** (nada de estados a medias,
  ADR `0006`). El E2E de historial falló exactamente ahí: el `200` de `POST /chat/stream` llega
  al abrir el stream, no al cerrarlo → el test ahora espera el cuerpo completo antes de recargar.
- El `done` trae la respuesta ya saneada por los guardrails, que puede diferir del texto
  token a token: el cliente reemplaza el parcial acumulado con el de `done` (spec lo explicita).
- Dos ADRs habían quedado con el mismo número (0004); se renumeró el de OpenSpec a `0005`.

**Resultado.** Rama `feat/openspec-adoption` con 2 commits (adopción + implementación).
Verificación: ruff + pytest `pytest_exit=0`; `tsc`/`eslint`/Vitest 38/38/`vite build`;
`e2e_check` con Ollama real ×2 (`e2e_exit=0`, 240 y 133 tokens incrementales); Playwright 9/9;
`openspec validate --strict --specs` 10/10; change archivado como
`2026-10-08-chat-sse-streaming` con +8 requirements en `ai-chat-assistant`.

**Lección.** Un desvío documentado (`PLAN` §7.3) se cierra mucho más limpio cuando primero se
convierte en un change con spec-delta: el contrato de eventos y el modo de cancelación quedan
decididos antes de escribir la primera línea de código, y el spec resultante es la evidencia.

### [20261009] F8: seed, E2E, hardening y auditoría final — completado

**Objetivo.** Cerrar el ciclo: datos de demostración, pruebas end-to-end de la UI, checklist de
`docs/SEGURIDAD.md` verificado contra el sistema corriendo y `README.md` final.

**Contexto para el agente.** `docs/PLAN-IMPLEMENTACION.md` §10 (entregables de F8) y
`docs/SEGURIDAD.md` §7 (checklist verificable). Cada ítem se marcó sólo después de comprobarlo
con `curl`, con un test o leyendo el código, no por intención.

**Prompts clave.**
1. *"Levantá el checklist de SEGURIDAD punto por punto contra el entorno real y aplicá los fixes
   de lo que no cierre; dejá explicitadas las deudas."*
2. *"El modelo no debe poder ejecutar escrituras: filtrá `WRITE_TOOLS` del catálogo, dejalo sólo
   en `proponer_accion` y hacé que el backend ejecute recién con confirmación explícita."*
3. *"Auditoría final: cruzá todo el código contra el plan, arreglá lo que esté desviado y cerrá
   con la verificación completa (pytest, ruff, tsc, eslint, Vitest, Playwright)."*

**Iteraciones y hallazgos.**
- **Fallo real del asistente:** el resultado de FastMCP llega como bloques de contenido
  (`[{"type":"text","text":"{...}"}]`), no como objeto; la confirmación devolvía JSON crudo
  embebido en el mensaje. Se agregó `_unwrap_result` que decodifica esos bloques (con test).
- **Seguridad sin implementar del todo:** el token en cliente se guardaba y se usaba sin mirar
  `exp` → ahora `tokenStore` descarta tokens vencidos y hay ADR `0004` que documenta por qué se
  eligió `localStorage` en vez de cookie `httpOnly`.
- **Agregados durante la auditoría:** límite de body (`413`), login local bloqueado en
  `ENV=production` con default `false`, `pattern` de email, `limit` acotado en reportes/stock,
  `exclude_unset` en proveedores y **celdas XLSX forzadas a texto** (openpyxl guarda `=1+1`
  como fórmula: hay que setear `data_type="s"`, el formato `@` solo no alcanza).
- **E2E de Playwright (4/4):** guard de rutas, login → dashboard, listado → detalle y descarga
  de CSV. Para el login E2E se usa el usuario local de emergencia del `.env`.
- **Verificación final:** backend 111 tests + `ruff` limpio; frontend `tsc` + `eslint` + 15 unit
  + 4 E2E; prueba manual del flujo completo de propuesta → confirmación → cliente creado en
  MongoDB con Ollama real.

**Lección.** El checklist de seguridad vale sólo si se ejecuta contra el sistema levantado:
tres de los ítems que daba por hechos (expiración del token en cliente, límite de body y
forzado de texto en XLSX) no estaban implementados hasta que se verificaron uno por uno.

### [20261008] F6 + F7: módulos de negocio, notificaciones, exportación y chat — completado

**Objetivo.** Implementar las pantallas de negocio del frontend (CU02–CU06, CU08), la exportación
que respeta los filtros de pantalla (CU10), la campana de notificaciones (CU09) y el asistente
lateral (CU07).

**Contexto para el agente.** Contrato de la API confirmado leyendo `backend/app/routers/*` y
`backend/app/schemas/*`; reglas de `frontend/AGENTS.md` (estado de servidor con TanStack Query,
estado de URL con search params, nunca copiar datos de servidor a `useState`).

**Prompts clave.**
1. *"Implementá proveedores, productos, clientes y órdenes como features, cada una con
   `api.ts`/`hooks.ts`/componentes y los cuatro estados por pantalla, reutilizando `DataTable`."*
2. *"Agregá el Dashboard consumiendo `/reports/*` con filtro de rango por fecha y KPIs navegables."*
3. *"Centralizá la exportación CSV/XLSX en un componente que reutilice los filtros activos y
   descargue el binario con el token Bearer."*
4. *"Implementá la campana de notificaciones con badge, panel y acciones masivas, y el ChatWidget
   lateral con restauración de historial y manejo de 503/429."*

**Iteraciones y hallazgos.**
- El build de F6 falló por un hook mal nombrado (`useStockAdjust` vs `useAdjustStock`) y por un
  `onSubmit` con tipo desalineado; se introdujo `ProductFormOutput` para separar el payload del
  formulario del modelo de dominio.
- La descarga de exportaciones **no** puede ser un `<a href>`: la sesión viaja en el header
  `Authorization`, así que se hace `GET` con `responseType: "blob"` y se dispara la descarga por
  `URL.createObjectURL`, respetando el `content-disposition`.
- El chat expone SSE (`POST /chat/stream`) con `POST /chat` como fallback; el frontend parsea los
  eventos y muestra la respuesta token a token, priorizando además el estado de "pensando", el render
  de `tool_calls` y el manejo de `429`/`503`.
- Se agregaron tests de la normalización de query params (`toQuery`), que es compartida por todos
  los listados y la exportación.

### [20261008] F5: shell del frontend (Vite + React + TS) — completado

**Objetivo.** Levantar el frontend (F5) con el modelo de sesión, el cliente HTTP endurecido y el
layout protegido, sin implementar todavía los módulos de negocio.

**Contexto para el agente.** `frontend/AGENTS.md` fija las reglas (estructura por feature,
cuatro estados por pantalla, sin comentarios, identificadores en inglés y textos en español) y
`docs/PLAN-IMPLEMENTACION.md` §7 lista los entregables de la fase.

**Prompts clave.**
1. *"Armá el scaffold Vite + React 19 + TS estricto + Tailwind v4 con Vitest y ESLint, y un cliente
   Axios con interceptores que normalicen 401/403/404/409/422/429/5xx."*
2. *"Implementá AuthProvider con persistencia del token y revalidación de sesión vía `/auth/me`,
   `ProtectedRoute` con estados loading/anónimo/autenticado y el layout con sidebar y header."*

**Iteraciones y hallazgos.**
- `formatDate` parseaba las fechas sólo-fecha (`YYYY-MM-DD`) como UTC y, al formatearlas en
  `America/Argentina/Buenos_Aires`, **retrocedían un día**. Se detectó con un test y se corrigió
  tratando el patrón de fecha pura de forma determinista.
- El `Spinner` dentro del `Button` necesitaba un tamaño menor; se resolvió por clase utilitaria.
- `erasableSyntaxOnly` no existe en TypeScript 5.6; se quitó del `tsconfig`.
- El primer `Input` con `forwardRef` quedó mal formado; se reescribió con una firma limpia.
- Ruta de callback OAuth (`/auth/callback?token=…`) implementada en el cliente; el backend aún
  devuelve el token como JSON, por lo que la redirección al SPA queda como refinamiento de CU01.

**Verificación.** `tsc --noEmit` sin errores, `vite build` correcto, `eslint .` limpio y tests de
Vitest verdes (formateo + guard de sesión). El backend completo sigue con su suite verde.

### [20260710] Cierre de F4: exportación CSV/XLSX y notificaciones — completado

**Objetivo.** Completar el backend de soporte (F4.2 y F4.3): exportación que respete los filtros
de pantalla (CU10) y el motor de notificaciones en plataforma (CU09).

**Contexto para el agente.** `docs/CASOS_DE_USO.md` §CU09 y §CU10 (catálogo de reglas y columnas),
el patrón de `repositories/` ya existente, y la regla "el export reutiliza la misma query del
listado" del `backend/AGENTS.md`.

**Prompts clave.**
1. *"Implementá `GET /exports/{entidad}.{csv|xlsx}` reutilizando las funciones de listado, sin
   paginación; CSV con BOM y montos planos, XLSX con openpyxl y formato de moneda."*
2. *"Implementá `GET /notifications`: recalculá las alertas de stock, envíos, cobros y órdenes
   incompletas, combinándolas con el estado de lectura/descarte por usuario."*

**Iteraciones y hallazgos.**
- Para CU09 faltaban en el modelo `Sale` los campos `ship_by` y `payment_due` que las reglas de
  envío y cobro dan por sentados. Se agregaron al modelo y a los schemas de creación/edición.
- El primer borrador del servicio de notificaciones usaba un alias de import inconsistente
  (`notif_repo` vs `notifications_repo`); el test lo cazó de inmediato (NameError).
- Regla de exclusión mutua para evitar duplicados: un producto en 0 genera `STOCK_AGOTADO` y
  **no** también `STOCK_MINIMO`; un cobro vencido genera `PAGO_VENCIDO` y no `PAGO_PENDIENTE`.
- Seguridad de export: además del rate limit, se neutraliza la **inyección de fórmulas** en CSV
  (celdas que empiezan con `=`, `+`, `-`, `@` se prefijan con `'`), con test propio.

**Verificación.** Paridad export↔listado por test (mismo filtro, mismo conjunto), BOM en CSV,
montos numéricos y `number_format` en XLSX, y **una prueba por cada regla de generación** de
alerta más las de estado leído/descartado. **101 tests verdes** y ruff limpio.

---

### [20261007] Endurecimiento: rate limit, headers, health y timestamps — completado

**Objetivo.** Cerrar los pendientes de seguridad de la rúbrica (rate limiting por endpoint,
headers de seguridad, CORS explícito) y corregir dos defectos de consistencia: documentos
creados sin `created_at`/`updated_at` y un `/health` que no reflejaba el estado de la IA.

**Contexto dado a la IA.** `docs/SEGURIDAD.md` §3.4 y §5.5, `docs/ARQUITECTURA.md` (tabla de
rate limit), el checklist no negociable de `AGENTS.md` §6 y el árbol de `backend/AGENTS.md`.

**Prompt (esencial).** *"Implementá el rate limiting por endpoint con `429` + `Retry-After`,
headers de seguridad, CORS con métodos/headers explícitos, y que `/health` reporte el estado
de Ollama. De paso, que todo documento creado persista `created_at` y `updated_at`."*

**Iteración.** 1) El rate limit se resolvió con un middleware propio
(`app/middleware/security.py`) en lugar de `slowapi`: el estado por ventana y la clave por
usuario/IP quedan en código explícito y **testeable** (se puede bajar un límite desde settings
y verificar el `429` sin tocar la app). Se quitó `slowapi` de `requirements.txt`.
2) El orden de middlewares importó: `RateLimit` → `SecurityHeaders` → `CORS`, para que la
respuesta `429` también salga con headers de seguridad y CORS. 3) En tests el rate limit se
desactiva por defecto (fixture `db`) y se reinicia el estado de ventanas.

**Resultado.** Middleware de headers + rate limit; `/health` con `{"status","services":{mongo,ollama}}`;
`created_at`/`updated_at` en `providers`, `clients`, `products` y `sales`; `tests/test_security.py`
(headers, HSTS en prod, `429`, health exento). **84 tests verdes** y ruff limpio.

**Lección.** Un límite "por endpoint" se defiere a un middleware que corre **antes** de la
autenticación: cuenta aunque el request termine en `401`. Eso está bien para frenar fuerza
bruta, pero obliga a keyear por IP (no por usuario) cuando aún no hay token. La clave se
degrada a usuario sólo si el Bearer es válido.

---

### [20261006] Servidor MCP propio + agente con tool-calling — completado

**Objetivo.** Que el asistente (CU07) actúe sobre el negocio exclusivamente a través de un
servidor MCP, y que ese servidor sea **código propio** (plano de producto, no sólo tooling).

**Contexto dado a la IA.** `AGENTS.md` §3.4 ("el asistente no toca la BD"), `docs/MCP.md`,
`backend/AGENTS.md` (capas), el patrón de tests de `donata-deco`, y la recomendación de
`langchain-mcp-adapters`.

**Prompt (esencial).** *"Implementá `donata-mcp` con FastMCP (stdio) exponiendo las operaciones
de negocio en español que envuelvan los `services`; y un agente que las consuma con
`MultiServerMCPClient`, con un bucle de tool-calling acotado y log de las herramientas usadas."*

**Iteración.** 1) Se expusieron las 12 tools envolviendo `services`, no repositorios.
2) Primer E2E real: el agente eligió bien la tool pero el `buscar_productos` falló con
`localhost:27017` — el subproceso MCP **no heredaba** `MONGO_URI` del `env_file` de compose.
→ Se agregó `_server_env()` que inyecta explícitamente `MONGO_URI`, `CHROMA_DIR`,
`OLLAMA_BASE_URL`, etc. al subproceso. 3) Se partió una línea larga del `SYSTEM_PROMPT` que
rompía ruff (line-length 100).

**Resultado.** `backend/app/mcp_server.py` (12 tools), `agent.py` (bucle de tool-calling,
`MAX_STEPS=6`), `assistant.py` (guardrails + historial + persistencia de `tool_calls`),
`POST /chat`. **80 tests verdes** y E2E real:

```
Respuesta: En tu catálogo actualmente hay ... con stock ...
Herramientas usadas: ['buscar_productos']
```

**Lección.** Un servidor MCP por **stdio** hereda el entorno del proceso padre de forma
implícita solo hasta cierto punto: si el agente lo lanza como subproceso, conviene pasar el
entorno **explícito** en lugar de confiar en el `.env`. Es un error silencioso: el agente
"funciona" pero las tools fallan por conexión.

---

### [20261005] RAG local sobre el manual operativo — completado

**Objetivo.** Responder preguntas sobre las reglas del negocio a partir de documentación,
sin inventar, y sin salir de la máquina.

**Contexto dado a la IA.** El ejemplo docente `rag-chat-static` (loader → splitter → embeddings
→ Chroma → chain LCEL) y la restricción de IA 100 % local.

**Prompt (esencial).** *"Espejá el pipeline del ejemplo pero con la arquitectura del proyecto:
`services/llm/vector_store.py` y `rag.py`, ingesta idempotente, embeddings HuggingFace
`all-MiniLM-L6-v2`."*

**Iteración.** La ingesta automática en el `lifespan` obligó a correr los embeddings en
`to_thread` para no bloquear el arranque. Se agregó una segunda colección (`donata_products`)
para la búsqueda semántica de productos, separada de la del manual.

**Resultado.** `backend/knowledge/manual-operativo.md` (12 fragmentos), `scripts/ingest_kb.py`
(`--force`, `--products`), chain LCEL con `temperature=0.1`. Verificado: preguntar *"¿Cómo se
calculan los precios mayoristas?"* devuelve la respuesta del manual, no del modelo.

**Lección.** Nunca mezclar en una misma colección el conocimiento estable (manual) con datos que
cambian (catálogo): se resetean e indexan por separado.

---

### [20261004] Historial de conversaciones — completado

**Objetivo.** Persistir los hilos y mensajes del chat para dar continuidad y dejar auditoría.

**Prompt (esencial).** *"Threads scoped por usuario, creación idempotente, borrado del hilo en
cascada sobre sus mensajes (es un chat: no aplica el `409` de integridad)."*

**Iteración.** Se decidió que el historial que se le entrega al modelo es acotado
(`CHAT_HISTORY_LIMIT`), no todo el hilo, para no inflar el prompt de un 7B.

**Resultado.** `services/chat_history.py`, `routers/chat.py`, `tests/test_chat_history.py`.

**Lección.** El chat es el único dominio del sistema donde el borrado en cascada es lo correcto;
la regla general del proyecto (borrar con referencias → `409`) tiene su excepción documentada.

---

### [20261003] Backend de negocio: servicios + routers — completado

**Objetivo.** Portar la lógica de negocio probada del sistema heredado, con los cambios de
alcance (sin roles, producto↔proveedor obligatorio, precio dual).

**Contexto dado a la IA.** `donata-deco/backend/app/routers/sales.py` y `models.py` como fuente
de reglas; `AGENTS.md` §3 como contrato.

**Prompt (esencial).** *"Portá la lógica, no el framework. Stock atómico con
`find_one_and_update` condicional, rollback total, movimientos inmutables."*

**Iteración.** La revisión adversarial encontró que el alta de producto no persistía bien
`provider_id` como ObjectId ni el `active=True` por defecto: se corrigió. El `422` de proveedor
inexistente y el `409` de borrado con referencias quedaron cubiertos por tests.

**Resultado.** `services/{providers,products,clients,sales,stock,reports}.py`, sus routers, y
tests de atomicidad, rollback, invariantes de saldo y reportes. **65 tests** al cerrar el hito.

**Lección.** El test de atomicidad de stock hay que escribirlo **antes**: es el invariante que
más fácil se rompe al "optimizar" una lectura.

---

### [20261002] Autenticación OAuth Google + JWT — completado

**Objetivo.** CU01: login con Google y sesión por JWT, sin roles.

**Prompt (esencial).** *"Flujo authorization-code con validación de `state`, upsert del usuario
por `google_sub`, rechazo de cuentas inactivas, y login local de emergencia."*

**Iteración.** Se verificó que el `state` inválido y el token expirado devuelvan `401`. El
`access_token` se valida con la librería de Google (`tokeninfo`) y se hace upsert por `sub`.

**Resultado.** `core/{errors,security}.py`, `services/auth.py`, `dependencies.py`,
`routers/auth.py`, `tests/test_auth.py`.

**Lección.** El `state` de OAuth no es opcional: sin validarlo, el callback es un CSRF.

---

### [20261001] Scaffolding: Docker + backend base — completado

**Objetivo.** Dejar `docker compose up` levantando API + Mongo, con health check y configuración
por entorno.

**Prompt (esencial).** *"Dockerfile python:3.12-slim, config con pydantic-settings que falla
rápido, `/health`, y montar `data/` para caches de modelos."*

**Iteración.** Se agregó `python-multipart`, `--no-deps` para correr tests sin re-levantar Mongo,
y el montaje de `data/hf_cache` para no re-descargar el modelo de embeddings en cada arranque.

**Resultado.** `docker-compose.yml`, `backend/Dockerfile`, `config.py`, `db.py`, `main.py`,
`/health` → ok.

**Lección.** Montar la caché de HuggingFace como volumen ahorra minutos de descarga por corrida
y evita fallos por red en la demo.

---

### [20260926] Especificación de los 10 casos de uso — completado

**Objetivo.** Definir los 10 casos de uso funcionales del sistema para presentarlos a
validación docente antes de desarrollar (requisito de la rúbrica).

**Contexto dado a la IA.** Rúbrica del TP, consignas del curso, y el sistema ya existente en
`donata-deco` (Streamlit + FastAPI + MongoDB) como fuente de las reglas de negocio reales.

**Prompt (esencial).** Definir 10 casos de uso cubriendo autenticación con Google, dashboard
con métricas y filtros de fechas, ABMs de productos/clientes/órdenes/proveedores, chat IA,
stock, notificaciones y exportación; cada uno con alcance frontend **y** backend.

**Iteración.** 1a versión → se agrega restricción de seguridad explícita y se eliminan los
roles de usuario (decisión del cliente). 2a versión → se incorpora que el producto siempre
tiene proveedor. 3a versión → el chat pasa a modelo local 7B. Cuarta → revisión de coherencia
interna (los criterios de aceptación de cada CU deben ser verificables con lo implementado).

**Resultado.** `docs/CASOS_DE_USO.md` + `docs/CASOS_DE_USO.pdf` (21 páginas, generado con
`scripts/md2pdf.py`, verificado).

**Lección.** Los casos de uso que se escriben **antes** de la implementación son un contrato
mucho más fuerte que los que se escriben después. Obligan a decidir antes de tener la tentación
de "después lo hago".

---

## 6. Estructura del README final

El `README.md` de la raíz tiene que ser la bitácora que pide la rúbrica. Estructura
propuesta:

```markdown
# Donata IA
1. Qué es el sistema (con captura de pantalla)
2. Arquitectura (diagrama + stack + por qué)
3. Los 10 casos de uso (enlace a docs/CASOS_DE_USO.md) + estado de cada uno
4. Puesta en marcha (docker compose up, variables de entorno, modelo de Ollama)
5. AI Engineering
   5.1 Herramientas y configuración del entorno
   5.2 Cómo se estructuró el contexto (AGENTS.md, agentes, skills)
   5.3 Prompts clave que hicieron que la implementación funcionara
   5.4 Iteraciones: qué falló y cómo se resolvió
   5.5 Loops de autocorrección
6. MCP: servidores, configuración y su rol
7. Seguridad
8. Estructura del repositorio
9. Tests
```

Las secciones 5 y 6 se alimentan de este documento y de `docs/MCP.md`. **No duplicar
contenido**: acá va el detalle, en el README se resume y se enlaza.

---

## 7. Anti-patrones evitados

| Anti-patrón | Por qué se evitó |
|---|---|
| Aceptar la primera respuesta sin verificar | Escribir plausible ≠ funcionar. El test es el judge |
| Un solo agente haciendo todo | El contexto mezclado degrada la calidad de cada parte |
| Contexto de 50 archivos "por las dudas" | Ruido: el agente pierde el hilo entre lo relevante y el ruido |
| Prompt sin restricciones explícitas | La IA aplica sus defaults, que no son los del dominio |
| Documentar al final | Una bitácora escrita de memoria no es una bitácora |
| Ignorar los fallos | Un fallo documentado vale más para la nota que un éxito silencioso |
| Meter la lógica de negocio en los componentes de React | Se pierde en el refactor y no se testea |
