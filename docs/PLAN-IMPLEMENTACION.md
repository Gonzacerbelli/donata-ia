# Plan de Implementaci�n - Donata IA

> Documento de trabajo. Se actualiza al cerrar cada fase. El estado vive ac� y en `AGENTS.md`.

---

## 0. Estado

| Fase | Descripci�n | Estado |
|---|---|---|
| **F0** | Bootstrap: estructura del repo, contexto para IA, PDF de casos de uso | ? **Completada** |
| **F1** | Validaci�n docente de los 10 casos de uso | ? **Completada** (feedback incorporado) |
| **F2** | Scaffolding: Docker, backend base (config, seguridad, modelos) | ? **Completada** |
| **F3** | Backend de negocio: auth, proveedores, productos, clientes, �rdenes, stock | ? **Completada** |
| **F4** | Backend de soporte: reports, historial de chat, RAG, servidor MCP + agente | ? **Completada** (incluye notificaciones y exports) |
| **F5** | Frontend: base, auth, layout | ? **Completada** |
| **F6** | Frontend: m�dulos de negocio (dashboard, productos, clientes, �rdenes, proveedores) | ? **Completada** |
| **F7** | Frontend: notificaciones, exportaci�n, chat IA | ? **Completada** |
| **F8** | Seed de datos, tests E2E, hardening, README final | ? **Completada** |
| **Ext** | M�dulo "Trabajo": tablero de �rdenes (extensi�n fuera de los 10 CU) | ? **Implementado** (changes `add-work-board` y `work-board-close-on-delivery`) |

**Leyenda:** ? pendiente � ? en curso � ? completada

---

## 1. Orden de ejecuci�n recomendado

El orden no es arbitrario. Cada fase deja el sistema en estado ejecutable y verificable.

```
F0 ? ??? F1 ? ??? F2 ??? F3 ??? F4 ??? F5 ??? F6 ??? F7 ??? F8
 bootstrap      infra      datos     reportes         shell      m�dulos     IA+extras   cierre
                                                            y n�cleo
```

**Regla:** no se empieza una fase hasta que la anterior tiene su verificaci�n pasando
(`pytest` verde en backend, `tsc` + `lint` limpios en frontend, `docker compose up` sano).

---

## 2. F0 - Bootstrap (? completada)

| Tarea | Entregable |
|---|---|
| Especificar los 10 casos de uso | `docs/CASOS_DE_USO.md` |
| Generar el PDF para validar | `docs/CASOS_DE_USO.pdf` (21 p�ginas) |
| Contexto maestro para IA | `AGENTS.md` |
| Documentos de soporte | `docs/{ARQUITECTURA,SEGURIDAD,AI-ENGINEERING,MCP,README-TPL}.md` |
| Configuraci�n de agentes | `opencode.json` + `.opencode/{agent,command,skills}` |
| Utilidad de impresi�n | `scripts/md2pdf.py` |
| Ignore + variables de entorno | `.gitignore`, `.env.example` |

---

## 3. F1 - Validaci�n docente (? en espera)

El usuario entrega `docs/CASOS_DE_USO.pdf` y espera el feedback.

**Mientras tanto, tareas que no dependen del feedback** (se pueden adelantar):

- [x] Levantar el esqueleto de Docker + `docker-compose.yml`.
- [ ] Configurar la conexi�n a MongoDB Atlas y verificar la conectividad.
- [ ] Descargar/verificar el modelo de Ollama y medir su velocidad de respuesta en CPU.
- [x] Registrar la app en Google Cloud Console y obtener las credenciales OAuth 2.0.
- [x] Portar los tests de `donata-deco/backend/tests` como base de la suite nueva.

> **Nota:** Mongo corre local en Docker (`mongodb://mongo:27017`); Atlas queda como alternativa
> documentada en el README, no configurada. El modelo est� descargado y verificado (E2E con
> Ollama real) pero **no se registr� una medici�n formal de latencia en CPU**.

**Si el docente pide cambios**, se actualizan `docs/CASOS_DE_USO.md`, se regenera el PDF con
`python scripts/md2pdf.py docs/CASOS_DE_USO.md docs/CASOS_DE_USO.pdf` y se contin�a.

---

## 4. F2 - Scaffolding

### 4.1 Infraestructura

| Tarea | Detalle |
|---|---|
| `docker-compose.yml` | Servicios `api` (FastAPI) y `web` (Vite dev server) + red + volumenes |
| `backend/Dockerfile` | `python:3.12-slim`, install deps, `uvicorn` en 8000 |
| `frontend/Dockerfile` | node para build + nginx para servir el bundle en prod |
| `backend/app/config.py` | `pydantic-settings`: lee `.env`, valida y falla r�pido si falta algo |
| `backend/app/db.py` | `AsyncIOMotorClient`, �ndices, ping en el startup |
| `backend/app/main.py` | `lifespan`, CORS, headers de seguridad, rate limit, manejo de errores global, health check |
| `.env.example` | Una variable por vez, con comentario del purpose |

### 4.2 Modelos de dominio

Portar de `donata-deco/backend/app/models.py`, con los cambios de alcance:

| Cambio | Detalle |
|---|---|
| `User` | **Quitar `role`.** Agregar `google_sub`, `picture`, `last_login_at`. `password_hash` pasa a opcional (s�lo para login local de emergencia). |
| `Product` | **`provider_id` obligatorio.** |
| `Client` | Sin cambios. |
| `Provider` | Sin cambios. |
| `Sale` | Agregar `ship_by` (fecha l�mite de env�o) y `payment_due` (vencimiento de cobro), que hacen falta para CU09. |
| `StockMove` | Sin cambios. Ya es la auditor�a que exige CU08. |
| `Notification` | Nuevo: `user_id`, `key` (hash estable de la condici�n), `type`, `severity`, `title`, `message`, `entity_type`, `entity_id`, `read`, `dismissed`, `created_at`. |

### 4.3 �ndices de MongoDB

Crear en el startup (idempotente):

- `users`: `{ google_sub: 1 }` �nico � `{ email: 1 }` �nico
- `products`: `{ name: 1 }` � `{ provider_id: 1 }` � `{ category: 1 }` � `{ stock: 1 }`
- `clients`: `{ name: 1 }` � `{ email: 1 }` � `{ phone: 1 }`
- `sales`: `{ date: -1 }` � `{ client_id: 1 }` � `{ status: 1 }`
- `stock_moves`: `{ product_id: 1, created_at: -1 }`
- `notifications`: `{ user_id: 1, key: 1 }` �nico

---

## 5. F3 - Backend de negocio

Orden dentro de la fase: primero los independentemente verificables, despu�s el n�cleo.

| # | Tarea | CU | Verificaci�n |
|---|---|---|---|
| 3.1 | Auth OAuth Google + JWT | CU01 | Test de flujo completo con `state` inv�lido, usuario inactivo, token expirado |
| 3.2 | CRUD de proveedores | CU06 | Tests CRUD + `409` con productos asociados |
| 3.3 | CRUD de productos con `provider_id` obligatorio | CU03 | Tests CRUD + `422` proveedor inexistente + filtros |
| 3.4 | CRUD de clientes | CU04 | Tests CRUD + `409` con �rdenes + b�squeda multi-campo |
| 3.5 | Servicio de stock (ajuste at�mico + historial) | CU08 | Tests de atomicidad, stock negativo, trazabilidad |
| 3.6 | �rdenes: alta con pricing dual e �tems mixtos | CU05 | Tests de rollback total ante stock insuficiente |
| 3.7 | �rdenes: pagos, cancelaci�n, borrado, re-cancelaci�n | CU05 | Tests de invariantes de saldo y de stock |
| 3.8 | Rate limiting y headers de seguridad aplicados | todos | Test de `429` y de headers presentes |

**Dependencias:** 3.5 antes que 3.6 y 3.7 (las �rdenes usan el servicio de stock).

---

## 6. F4 - Backend de soporte (? completada)

| # | Tarea | CU | Verificaci�n |
|---|---|---|---|
| 4.1 | Reportes con rango de fechas | CU02 | Tests de agregaciones con fixtures de datos conocidos |
| 4.2 | Notificaciones (c�lculo + estado le�do) | CU09 | Tests de cada regla de generaci�n de alerta |
| 4.3 | Exportaci�n CSV y XLSX reutilizando las queries de listado | CU10 | Test de paridad: export == lo que muestra el listado filtrado |
| 4.4 | Chat IA: agente LangChain + Ollama + tools | CU07 | Test con Ollama mockeado + test manual con el modelo real |
| 4.5 | Health check de Ollama + degradaci�n elegante | CU07 | Test de Ollama ca�do ? `503` y el resto sigue operando |
| 4.6 | Servidor MCP propio (`donata-mcp`) + agente con tool-calling por MCP + RAG sobre el manual operativo | CU07 | Tests por stdio real + E2E con Ollama real (`scripts/e2e_check.py`) |

**Estado F4 (hito cerrado).** Implementado y en `main`: guardrails, historial de chat en Mongo,
RAG local (Chroma + embeddings HuggingFace), el servidor MCP `donata-mcp` con 12 herramientas
(consumido por el agente v�a `langchain-mcp-adapters`), **notificaciones** (CU09) y **exportaci�n
CSV/XLSX** (CU10). **101 tests verdes** y chequeo E2E real con Ollama (`qwen2.5:7b-instruct`).

- **4.2 Notificaciones.** `GET /notifications` recalcula las alertas del negocio en cada consulta
  (stock, env�os, cobros, orden incompleta) y las combina con el estado por usuario
  (`notification_states`): `PATCH /notifications/{id}`, `POST /notifications/read-all` y
  `POST /notifications/dismiss-all`. Reglas del cat�logo CU09 con severidad alta/media/baja.
- **4.3 Exportaci�n.** `GET /exports/{entidad}.{csv|xlsx}` reutiliza **exactamente** las mismas
  queries de listado (mismos filtros y orden, sin paginaci�n), con paridad verificada por test.
  CSV en UTF-8 con BOM y montos planos; XLSX con openpyxl y formato de moneda. L�mite de 10 000
  filas ? `422`.

**Sobre 4.4.** La parte m�s delicate. Secuencia:

1. Definir el **system prompt** versionado (`app/services/llm/prompts.py`) con las 10 reglas duras.
2. Implementar las tools como funciones Pydantic que llaman a los **services**, no a los routers.
3. Configurar `ChatOllama` con `temperature` baja y `OLLAMA_BASE_URL` configurable.
4. Probar el loop tool-calling contra el modelo real y **ajustar el prompt** hasta que
  yll reliably elija la tool correcta.
5. Agregar streaming SSE. ? `POST /chat/stream` (eventos `start`/`token`/`tool_start`/`tool_end`/
   `pending_action`/`done`/`error`), con `POST /chat` intacto como fallback.
6. Fallback: si Ollama no responde, `503` con mensaje claro.

> ?? Los modelos de 7B en CPU son la parte m�s lenta del sistema. Dise�ar la UI para que el
> chat muestre un estado de "pensando" y no bloquee el resto de la app.

---

## 7. F5 - Frontend base (? completada)

| Tarea | Detalle | Estado |
|---|---|---|
| Vite + React + TS | Configuraci�n estricta de TypeScript (`strict`, sin `any`) | ? |
| Tailwind + componentes base | Tema, tokens de color, tipograf�a | ? |
| Cliente HTTP | Axios con interceptores: token, `401` ? logout, `429` ? `Retry-After`, normalizaci�n de errores | ? |
| Router | Rutas p�blicas y protegidas con guard | ? |
| Estado de sesi�n | Contexto de auth + persistencia del token + expiraci�n en cliente | ? |
| Layout | Sidebar de navegaci�n, header con campana (placeholder F7), contenedor responsive | ? |
| Formateo | ARS sin decimales, fechas DD/MM/AAAA, timezone Argentina | ? |

**Estado F5.** Proyecto Vite + React 19 + TS + Tailwind v4 en `frontend/`. Cliente HTTP con
normalizaci�n de errores (`ApiError`) y handlers por c�digo; `AuthProvider` con persistencia
en `localStorage` y revalidaci�n de sesi�n; `ProtectedRoute` con estados loading/an�nimo/autenticado;
layout con sidebar y header; componentes reutilizables (`Button`, `Input`, `Select`, `Modal`,
`DataTable` con los cuatro estados: cargando/vac�o/error/datos). Login local funcional y arranque
del flujo OAuth de Google. Verificado con `tsc --noEmit`, `vite build`, `eslint` y Vitest.

---

## 8. F6 - M�dulos de negocio (frontend)

| # | M�dulo | CU |
|---|---|---|
| 6.1 | Dashboard: KPIs, filtro de rango, tablas de detalle, KPIs navegables | CU02 |
| 6.2 | Proveedores: grilla, filtros, formulario | CU06 |
| 6.3 | Productos: grilla, filtros, formulario con proveedor obligatorio, ajuste de stock, historial de movimientos | CU03 � CU08 |
| 6.4 | Clientes: grilla, b�squeda, formulario, resumen de actividad | CU04 |
| 6.5 | �rdenes: listado con filtros, creaci�n con �tems mixtos, detalle, pagos, estados | CU05 |
| 6.6 | Exportaci�n: botones CSV/XLSX que reutilizan los filtros activos | CU10 |

**Estado F6.** Implementado bajo `frontend/src/features/`: `providers` (CU06), `products` (CU03 + CU08
con ajuste de stock e historial de movimientos), `clients` (CU04 con resumen de actividad), `orders`
(CU05 con listado filtrado, creaci�n de �tems mixtos, detalle, pagos y estados) y `dashboard` (CU02
con KPIs navegables de `/reports/*`, filtro de rango por fecha y tablas de productos m�s vendidos,
stock bajo y valor de inventario). La exportaci�n (CU10) se centraliza en `ExportButtons`, que
reutiliza los filtros activos de cada listado y descarga el binario con el token de sesi�n. Cada
pantalla respeta los cuatro estados (cargando/vac�o/error/datos). Verificado con `tsc --noEmit`,
`vite build`, `eslint` y Vitest.

---

## 9. F7 - Notificaciones y chat IA (frontend)

| # | Tarea | CU |
|---|---|---|
| 7.1 | Campana con badge + panel lateral + acciones masivas | CU09 |
| 7.2 | `ChatWidget` lateral, disponible desde cualquier pantalla | CU07 |
| 7.3 | Streaming de la respuesta, render de tablas, deep links a la entidad | CU07 ? |
| 7.4 | Estado de "pensando", manejo de `503` (Ollama ca�do) y de `429` | CU07 |

**Estado F7.** `NotificationBell` en el header con badge de no le�dos, panel agrupado por severidad,
acciones masivas (marcar le�das / descartar todo) y deep links a la entidad (`sale` ? detalle de
orden, `product` ? productos); se refresca cada 60 s. El `ChatWidget` est� disponible desde cualquier
 pantalla: el hilo activo se resuelve **por usuario contra Mongo** (`GET /chat/threads`, con la clave
de `localStorage` s�lo como preferencia - si no le pertenece al usuario se cae al hilo m�s reciente),
restaura el historial v�a `GET /chat/threads/{id}/messages`, muestra el estado "pensando", renderiza
los `tool_calls` y ofrece un reintento controlado ante `429` (`Retry-After`) y un mensaje claro ante
`503` (Ollama ca�do).

**7.3 (streaming).** El chat se sirve por `POST /chat/stream` (SSE): el frontend parsea los frames
(`start`, `token`, `tool_start`, `tool_end`, `pending_action`, `done`, `error`), muestra la respuesta
token a token con abort al cerrar el widget y revalida el historial al terminar. `POST /chat` sigue
disponible como fallback no-streaming. La cancelaci�n del cliente no persiste el turno.

---

## 10. F8 - Cierre (? completada)

| Tarea | Detalle | Estado |
|---|---|---|
| Seed de datos | `backend/scripts/seed_demo.py`: 4 proveedores, 15 productos de macram�, 10 clientes y ~48 �rdenes repartidas en el �ltimo a�o, con pagos, env�os y estados variados | ? |
| Tests E2E | Playwright en `frontend/e2e/`: guard de rutas, login ? dashboard, listado de �rdenes ? detalle, descarga de exportaci�n CSV (4/4 verdes) | ? |
| Hardening | Checklist de `docs/SEGURIDAD.md` verificado contra el entorno levantado; fixes aplicados durante la auditor�a (ver abajo) | ? |
| Documentaci�n | `README.md` final seg�n `docs/README-TPL.md` (stack, puesta en marcha, 10 CU, AI Engineering, MCP, seguridad, tests) | ? |
| Verificaci�n final | Backend 111 tests + ruff � frontend `tsc` + eslint + 15 unit + 4 E2E � auditor�a punto por punto del plan | ? |

### Fixes de la auditor�a final

- **Confirmaci�n del chat (5.2):** el modelo ya no ve `WRITE_TOOLS`; s�lo puede proponer con
  `proponer_accion` y el backend ejecuta reci�n en `POST /chat/confirm` (TTL 10 min). Salida MCP
  normalizada para que la respuesta sea legible.
- **Token en cliente:** `tokenStore` decodifica `exp` y descarta tokens vencidos
  (`frontend/src/lib/token.ts`), con ADR `docs/adr/0004-token-de-sesion-en-localstorage.md`.
- **L�mite de cuerpo:** `413` para bodies > 2 MB (`app/middleware/security.py`).
- **Login local:** default `false` y bloqueado cuando `ENV=production`, adem�s de la flag.
- **XLSX:** celdas de texto forzadas a `data_type="s"` + formato `@` (inyecci�n de f�rmula).
- **Validaci�n de entrada:** `pattern` de email en los schemas; `exclude_unset` en proveedores;
  `limit` acotado en reportes y movimientos de stock.
- **`.env.example`:** sin plantillas que parezcan credenciales reales.
- **UI:** chips de `tool_calls` leen `name` del tool call (mostraban siempre "consulta").

---

## 11. Trazabilidad CU ? tareas

| CU | Backend | Frontend | Seeds |
|---|---|---|---|
| CU01 � Auth OAuth Google | 3.1 | 5 (auth) | usuario admin |
| CU02 � Dashboard | 4.1 | 6.1 | �rdenes con fechas variadas |
| CU03 � ABM Productos | 3.3 | 6.3 | productos con proveedor |
| CU04 � ABM Clientes | 3.4 | 6.4 | clientesDeclared |
| CU05 � ABM �rdenes | 3.6 � 3.7 | 6.5 | �rdenes + pagos |
| CU06 � ABM Proveedores | 3.2 | 6.2 | proveedores |
| CU07 � Chat IA | 4.4 � 4.5 | 7.2 � 7.3 � 7.4 | - |
| CU08 � Stock | 3.5 | 6.3 | stock bajo en algunos productos |
| CU09 � Notificaciones | 4.2 | 7.1 | �rdenes con `ship_by` vencido |
| CU10 � Exportaci�n | 4.3 | 6.6 | - |

---

## 12. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigaci�n |
|---|---|---|
| El modelo 7B en CPU no sigue bien tool-calling | CU07 no cumple | Prompt estructurado en secciones � pocas tools bien descritas � `qwen2.5:7b-instruct` (el m�s fiel) � fallback a interpretaci�n por intenci�n si el tool-calling falla |
| Ollama no levanta dentro de Docker | Chat inaccesible | `host.docker.internal:11434` � documentar ambos modos � health check |
| MongoDB Atlas sin IP whitelisted | Backend no conecta | Verificar la whitelist antes de F2 � documentar |
| Cambio de alcance pedido por el docente | Retrabajo | Los CU est�n en un solo archivo versionado, f�ciles de actualizar � regenerar el PDF con un comando |
| �tomos de stock mal implementados | Inconsistencia de datos | Test dedicado de concurrencia en 3.5 � `find_one_and_update` condicional, nunca leer-modificar-escribir |
| Exportaci�n que no coincide con el listado | Incumplimiento de CU10 | Test de paridad: misma query, mismos filtros, mismo orden |
| Google OAuth en desarrollo suele dar problemas | Fricci�n en CU01 | Verificar redirect URIs exacto � tener login local de emergencia en dev |

---

## 13. C�mo se documenta el avance

Al cerrar cada tarea:

- [ ] Marcar la fase en la tabla de la secci�n 0.
- [ ] Agregar la entrada correspondiente en `docs/AI-ENGINEERING.md` (qu� se pidi�, qu� fall�, c�mo se resolvi�).
- [ ] Si hubo una decisi�n t�cnica no obvia, escribir un ADR en `docs/adr/`.
- [ ] Commit con mensaje en espa�ol describiendo el **por qu�**, no s�lo el **qu�**.

---

## 14. Ext - M�dulo "Trabajo"

Extensi�n **fuera de los 10 casos de uso validados**. Se apoya en CU05 (�rdenes) sin modificar la
entidad `Sale`; un tercer eje independiente del cumplimiento y la cobranza. Changes OpenSpec:
`openspec/changes/add-work-board/` (implementaci�n) y `openspec/changes/work-board-close-on-delivery/`
(regla de cierre autom�tico).

- **Backend:** colecci�n `work_items` (1:1 con `sales`, creada por *upsert*), modelo `WorkItem` +
  `WorkComment`, `repositories/work_items.py` (agregaci�n `$lookup` con defaults), `services/work.py`,
  routers `work` y `users`. Endpoints: `GET /work-items` (filtros `status`/`priority`/`assigned_to` y
  `date_sort`), `PATCH /work-items/{sale_id}` (estado, prioridad, asignaci�n), `POST
  /work-items/{sale_id}/comments`, `GET /users` (activos). Estados `pendiente|en_curso|bloqueado|
  terminado`; prioridad `alta|media|baja`; asignaci�n a cualquier usuario activo.
- **Frontend:** feature `work-board` (`/trabajo` en el sidebar) con cuatro columnas, tarjetas con
  resumen de �tems, prioridad, asignado y comentarios, drag & drop con `@dnd-kit/core`, filtros/orden
  en la URL (`sort`, `priority`, `assigned`) y `CommentModal`.
- **Reglas:** no modifica el estado de cumplimiento, los pagos ni el stock de la orden; sin roles;
  comentarios append-only con snapshot del autor; fechas UTC; el tablero muestra s�lo �rdenes no
  `entregado`/`cancelado`; al entregar la orden la tarjeta pasa a `terminado` (y vuelve a `pendiente`
  si se reabre) y las tarjetas de entregadas/canceladas quedan congeladas (`404`). La regla es
  unidireccional: una tarjeta `terminado` jam�s entrega la orden.
- **Verificaci�n:** `backend/tests/test_work_items.py` y `test_users.py`; Vitest del feature y E2E
  `frontend/e2e/trabajo.spec.ts`.
- **Fuera de alcance:** tools MCP del tablero, tiempo real, paginaci�n, orden manual por columna.
  `docs/CASOS_DE_USO.md` **no se modifica**.
