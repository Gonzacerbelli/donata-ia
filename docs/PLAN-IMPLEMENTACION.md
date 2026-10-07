# Plan de Implementación — Donata IA

> Documento de trabajo. Se actualiza al cerrar cada fase. El estado vive acá y en `AGENTS.md`.

---

## 0. Estado

| Fase | Descripción | Estado |
|---|---|---|
| **F0** | Bootstrap: estructura del repo, contexto para IA, PDF de casos de uso | ✅ **Completada** |
| **F1** | Validación docente de los 10 casos de uso | ✅ **Completada** (feedback incorporado) |
| **F2** | Scaffolding: Docker, backend base (config, seguridad, modelos) | ✅ **Completada** |
| **F3** | Backend de negocio: auth, proveedores, productos, clientes, órdenes, stock | ✅ **Completada** |
| **F4** | Backend de soporte: reports, historial de chat, RAG, servidor MCP + agente | ✅ **Completada** (notificaciones y exports pendientes) |
| **F5** | Frontend: base, auth, layout | ⬜ Pendiente |
| **F6** | Frontend: módulos de negocio (dashboard, productos, clientes, órdenes, proveedores) | ⬜ Pendiente |
| **F7** | Frontend: notificaciones, exportación, chat IA | ⬜ Pendiente |
| **F8** | Seed de datos, tests E2E, hardening, README final | ⬜ Pendiente |

**Leyenda:** ⬜ pendiente · ⏳ en curso · ✅ completada

---

## 1. Orden de ejecución recomendado

El orden no es arbitrario. Cada fase deja el sistema en estado ejecutable y verificable.

```
F0 ✅ ──▶ F1 ⏳ ──▶ F2 ──▶ F3 ──▶ F4 ──▶ F5 ──▶ F6 ──▶ F7 ──▶ F8
 bootstrap      infra      datos     reportes         shell      módulos     IA+extras   cierre
                                                            y núcleo
```

**Regla:** no se empieza una fase hasta que la anterior tiene su verificación pasando
(`pytest` verde en backend, `tsc` + `lint` limpios en frontend, `docker compose up` sano).

---

## 2. F0 — Bootstrap (✅ completada)

| Tarea | Entregable |
|---|---|
| Especificar los 10 casos de uso | `docs/CASOS_DE_USO.md` |
| Generar el PDF para validar | `docs/CASOS_DE_USO.pdf` (21 páginas) |
| Contexto maestro para IA | `AGENTS.md` |
| Documentos de soporte | `docs/{ARQUITECTURA,SEGURIDAD,AI-ENGINEERING,MCP,README-TPL}.md` |
| Configuración de agentes | `opencode.json` + `.opencode/{agent,command,skills}` |
| Utilidad de impresión | `scripts/md2pdf.py` |
| Ignore + variables de entorno | `.gitignore`, `.env.example` |

---

## 3. F1 — Validación docente (⏳ en espera)

El usuario entrega `docs/CASOS_DE_USO.pdf` y espera el feedback.

**Mientras tanto, tareas que no dependen del feedback** (se pueden adelantar):

- [ ] Levantar el esqueleto de Docker + `docker-compose.yml`.
- [ ] Configurar la conexión a MongoDB Atlas y verificar la conectividad.
- [ ] Descargar/verificar el modelo de Ollama y medir su velocidad de respuesta en CPU.
- [ ] Registrar la app en Google Cloud Console y obtener las credenciales OAuth 2.0.
- [ ] Portar los tests de `donata-deco/backend/tests` como base de la suite nueva.

**Si el docente pide cambios**, se actualizan `docs/CASOS_DE_USO.md`, se regenera el PDF con
`python scripts/md2pdf.py docs/CASOS_DE_USO.md docs/CASOS_DE_USO.pdf` y se continúa.

---

## 4. F2 — Scaffolding

### 4.1 Infraestructura

| Tarea | Detalle |
|---|---|
| `docker-compose.yml` | Servicios `api` (FastAPI) y `web` (Vite dev server) + red + volumenes |
| `backend/Dockerfile` | `python:3.12-slim`, install deps, `uvicorn` en 8000 |
| `frontend/Dockerfile` | node para build + nginx para servir el bundle en prod |
| `backend/app/config.py` | `pydantic-settings`: lee `.env`, valida y falla rápido si falta algo |
| `backend/app/db.py` | `AsyncIOMotorClient`, índices, ping en el startup |
| `backend/app/main.py` | `lifespan`, CORS, headers de seguridad, rate limit, manejo de errores global, health check |
| `.env.example` | Una variable por vez, con comentario del purpose |

### 4.2 Modelos de dominio

Portar de `donata-deco/backend/app/models.py`, con los cambios de alcance:

| Cambio | Detalle |
|---|---|
| `User` | **Quitar `role`.** Agregar `google_sub`, `picture`, `last_login_at`. `password_hash` pasa a opcional (sólo para login local de emergencia). |
| `Product` | **`provider_id` obligatorio.** |
| `Client` | Sin cambios. |
| `Provider` | Sin cambios. |
| `Sale` | Agregar `ship_by` (fecha límite de envío) y `payment_due` (vencimiento de cobro), que hacen falta para CU09. |
| `StockMove` | Sin cambios. Ya es la auditoría que exige CU08. |
| `Notification` | Nuevo: `user_id`, `key` (hash estable de la condición), `type`, `severity`, `title`, `message`, `entity_type`, `entity_id`, `read`, `dismissed`, `created_at`. |

### 4.3 Índices de MongoDB

Crear en el startup (idempotente):

- `users`: `{ google_sub: 1 }` único · `{ email: 1 }` único
- `products`: `{ name: 1 }` · `{ provider_id: 1 }` · `{ category: 1 }` · `{ stock: 1 }`
- `clients`: `{ name: 1 }` · `{ email: 1 }` · `{ phone: 1 }`
- `sales`: `{ date: -1 }` · `{ client_id: 1 }` · `{ status: 1 }`
- `stock_moves`: `{ product_id: 1, created_at: -1 }`
- `notifications`: `{ user_id: 1, key: 1 }` único

---

## 5. F3 — Backend de negocio

Orden dentro de la fase: primero los independentemente verificables, después el núcleo.

| # | Tarea | CU | Verificación |
|---|---|---|---|
| 3.1 | Auth OAuth Google + JWT | CU01 | Test de flujo completo con `state` inválido, usuario inactivo, token expirado |
| 3.2 | CRUD de proveedores | CU06 | Tests CRUD + `409` con productos asociados |
| 3.3 | CRUD de productos con `provider_id` obligatorio | CU03 | Tests CRUD + `422` proveedor inexistente + filtros |
| 3.4 | CRUD de clientes | CU04 | Tests CRUD + `409` con órdenes + búsqueda multi-campo |
| 3.5 | Servicio de stock (ajuste atómico + historial) | CU08 | Tests de atomicidad, stock negativo, trazabilidad |
| 3.6 | Órdenes: alta con pricing dual e ítems mixtos | CU05 | Tests de rollback total ante stock insuficiente |
| 3.7 | Órdenes: pagos, cancelación, borrado, re-cancelación | CU05 | Tests de invariantes de saldo y de stock |
| 3.8 | Rate limiting y headers de seguridad aplicados | todos | Test de `429` y de headers presentes |

**Dependencias:** 3.5 antes que 3.6 y 3.7 (las órdenes usan el servicio de stock).

---

## 6. F4 — Backend de soporte

| # | Tarea | CU | Verificación |
|---|---|---|---|
| 4.1 | Reportes con rango de fechas | CU02 | Tests de agregaciones con fixtures de datos conocidos |
| 4.2 | Notificaciones (cálculo + estado leído) | CU09 | Tests de cada regla de generación de alerta |
| 4.3 | Exportación CSV y XLSX reutilizando las queries de listado | CU10 | Test de paridad: export == lo que muestra el listado filtrado |
| 4.4 | Chat IA: agente LangChain + Ollama + tools | CU07 | Test con Ollama mockeado + test manual con el modelo real |
| 4.5 | Health check de Ollama + degradación elegante | CU07 | Test de Ollama caído → `503` y el resto sigue operando |
| 4.6 | Servidor MCP propio (`donata-mcp`) + agente con tool-calling por MCP + RAG sobre el manual operativo | CU07 | Tests por stdio real + E2E con Ollama real (`scripts/e2e_check.py`) |

**Estado F4 (cierre de hito).** Implementado y en `main`: guardrails, historial de chat en Mongo,
RAG local (Chroma + embeddings HuggingFace) y el servidor MCP `donata-mcp` con 12 herramientas,
consumido por el agente mediante `langchain-mcp-adapters`. **80 tests verdes** y chequeo E2E real
con Ollama (`qwen2.5:7b-instruct`). Notificaciones (4.2) y exportación (4.3) quedan pendientes.

**Sobre 4.4.** La parte más delicate. Secuencia:

1. Definir el **system prompt** versionado (`app/services/llm/prompts.py`) con las 10 reglas duras.
2. Implementar las tools como funciones Pydantic que llaman a los **services**, no a los routers.
3. Configurar `ChatOllama` con `temperature` baja y `OLLAMA_BASE_URL` configurable.
4. Probar el loop tool-calling contra el modelo real y **ajustar el prompt** hasta que
  yll reliably elija la tool correcta.
5. Agregar streaming SSE.
6. Fallback: si Ollama no responde, `503` con mensaje claro.

> ⚠️ Los modelos de 7B en CPU son la parte más lenta del sistema. Diseñar la UI para que el
> chat muestre un estado de "pensando" y no bloquee el resto de la app.

---

## 7. F5 — Frontend base

| Tarea | Detalle |
|---|---|
| Vite + React + TS | Configuración estricta de TypeScript |
| Tailwind + componentes base | Tema, tokens de color, tipografía |
| Cliente HTTP | Axios o fetch con interceptores: token, `401` → logout, `429` → `Retry-After`, normalización de errores |
| Router | Rutas públicas y protegidas con guard |
| Estado de sesión | Contexto de auth + persistencia del token + expiración en cliente |
| Layout | Sidebar de navegación, header con campana de notificaciones, contenedor responsive |
| Formateo | ARS sin decimales, fechas DD/MM/AAAA, timezone Argentina |

---

## 8. F6 — Módulos de negocio (frontend)

| # | Módulo | CU |
|---|---|---|
| 6.1 | Dashboard: KPIs, filtro de rango, tablas de detalle, KPIs navegables | CU02 |
| 6.2 | Proveedores: grilla, filtros, formulario | CU06 |
| 6.3 | Productos: grilla, filtros, formulario con proveedor obligatorio, ajuste de stock, historial de movimientos | CU03 · CU08 |
| 6.4 | Clientes: grilla, búsqueda, formulario, resumen de actividad | CU04 |
| 6.5 | Órdenes: listado con filtros, creación con ítems mixtos, detalle, pagos, estados | CU05 |
| 6.6 | Exportación: botones CSV/XLSX que reutilizan los filtros activos | CU10 |

---

## 9. F7 — Notificaciones y chat IA (frontend)

| # | Tarea | CU |
|---|---|---|
| 7.1 | Campana con badge + panel lateral + acciones masivas | CU09 |
| 7.2 | `ChatWidget` lateral, disponible desde cualquier pantalla | CU07 |
| 7.3 | Streaming de la respuesta, render de tablas, deep links a la entidad | CU07 |
| 7.4 | Estado de "pensando", manejo de `503` (Ollama caído) y de `429` | CU07 |

---

## 10. F8 — Cierre

| Tarea | Detalle |
|---|---|
| Seed de datos | Script de datos de demostración realistas (productos de macramé, clientes, órdenes con fechas repartidas en el último año) para que el dashboard muestre algo significativo |
| Tests E2E | Playwright sobre los flujos críticos: login, crear orden, registrar pago, exportar, chat |
| Hardening | Revisión de seguridad de `docs/SEGURIDAD.md` punto por punto |
| Documentación | `README.md` final: arquitectura, 10 CU, bitácora de AI Engineering, MCP |
| Verificación final | Los 10 CU con sus criterios de aceptación marcados |

---

## 11. Trazabilidad CU → tareas

| CU | Backend | Frontend | Seeds |
|---|---|---|---|
| CU01 · Auth OAuth Google | 3.1 | 5 (auth) | usuario admin |
| CU02 · Dashboard | 4.1 | 6.1 | órdenes con fechas variadas |
| CU03 · ABM Productos | 3.3 | 6.3 | productos con proveedor |
| CU04 · ABM Clientes | 3.4 | 6.4 | clientesDeclared |
| CU05 · ABM Órdenes | 3.6 · 3.7 | 6.5 | órdenes + pagos |
| CU06 · ABM Proveedores | 3.2 | 6.2 | proveedores |
| CU07 · Chat IA | 4.4 · 4.5 | 7.2 · 7.3 · 7.4 | — |
| CU08 · Stock | 3.5 | 6.3 | stock bajo en algunos productos |
| CU09 · Notificaciones | 4.2 | 7.1 | órdenes con `ship_by` vencido |
| CU10 · Exportación | 4.3 | 6.6 | — |

---

## 12. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El modelo 7B en CPU no sigue bien tool-calling | CU07 no cumple | Prompt estructurado en secciones · pocas tools bien descritas · `qwen2.5:7b-instruct` (el más fiel) · fallback a interpretación por intención si el tool-calling falla |
| Ollama no levanta dentro de Docker | Chat inaccesible | `host.docker.internal:11434` · documentar ambos modos · health check |
| MongoDB Atlas sin IP whitelisted | Backend no conecta | Verificar la whitelist antes de F2 · documentar |
| Cambio de alcance pedido por el docente | Retrabajo | Los CU están en un solo archivo versionado, fáciles de actualizar · regenerar el PDF con un comando |
| Átomos de stock mal implementados | Inconsistencia de datos | Test dedicado de concurrencia en 3.5 · `find_one_and_update` condicional, nunca leer-modificar-escribir |
| Exportación que no coincide con el listado | Incumplimiento de CU10 | Test de paridad: misma query, mismos filtros, mismo orden |
| Google OAuth en desarrollo suele dar problemas | Fricción en CU01 | Verificar redirect URIs exacto · tener login local de emergencia en dev |

---

## 13. Cómo se documenta el avance

Al cerrar cada tarea:

- [ ] Marcar la fase en la tabla de la sección 0.
- [ ] Agregar la entrada correspondiente en `docs/AI-ENGINEERING.md` (qué se pidió, qué falló, cómo se resolvió).
- [ ] Si hubo una decisión técnica no obvia, escribir un ADR en `docs/adr/`.
- [ ] Commit con mensaje en español describiendo el **por qué**, no sólo el **qué**.
