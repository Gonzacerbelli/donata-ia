# AGENTS.md — Donata IA

> **Este archivo es el punto de entrada de contexto para cualquier agente de IA que trabaje en
> este repositorio.** Antes de tocar código, leelo completo. No te saltees las reglas de aquí:
> son decisiones ya tomadas y validadas con el usuario, no sugerencias.

---

## 1. Qué es este proyecto

**Donata IA** — sistema web de gestión interna para **DonataDeco**, un emprendimiento argentino
de macramé y decoración del hogar. Reemplaza la operatoria en planillas Excel mensuales y
pedidos manuscritos.

Es el **Trabajo Práctico Integrador** de una Diplomatura en Desarrollo y Arquitectura de
Agentes de IA. La nota se compone de:

| Criterio | Puntos | Qué exige |
|---|---|---|
| Funcionalidad del sistema | 3 | 7 de 10 casos de uso resueltos, interactivos, sin errores críticos |
| Esquema de trabajo y AI Engineering | 3 | Uso efectivo de herramientas de desarrollo asistido, contexto bien guiado |
| Documentación (README) | 1 | README como bitácora: arquitectura, 10 CU, prompts clave, iteraciones |
| Implementación MCP | 1 | ≥ 2 servidores MCP, ≥ 1 externo |
| Chatbot integrado con LangChain | 2 | Chat funcional dentro de la app web |

**El foco de la evaluación es la ingeniería del proceso, no la estética del código.** Eso no
significa escribir código descuidado: significa que el repositorio debe *demostrar* que hubo
orquestación de agentes, prompts deliberados, iteraciones y verificación automatizada.

---

## 2. Estado actual (leer antes de actuar)

| Ítem | Estado |
|---|---|
| Especificación de los 10 casos de uso | ✅ **Completa** — `docs/CASOS_DE_USO.md` y `docs/CASOS_DE_USO.pdf` |
| Validación docente de los CU | ⏳ **Pendiente** (el feedback llegó y se incorporó al alcance) |
| Estructura del repo | ✅ Creada (carpetas + `.gitignore` + `.env.example`) |
| Configuración de agentes/IA | ✅ `AGENTS.md` + `opencode.json` + `.opencode/{agent,command,skills}` |
| Docker / compose | ✅ `docker-compose.yml` (api + mongo) + `backend/Dockerfile` |
| Backend FastAPI | ✅ Núcleo + negocio + soporte: auth, proveedores, productos, clientes, ventas, stock, reportes, historial de chat |
| IA: RAG + agente MCP | ✅ `donata-mcp` (12 tools) + agente LangChain con tool-calling + RAG (Chroma) — E2E real con Ollama |
| Frontend React | ✅ F5–F7: auth, dashboard, proveedores, productos, clientes, órdenes, notificaciones, chat |
| Seed / datos de prueba | ✅ `backend/scripts/seed_demo.py` (productos, clientes y órdenes del último año) |
| Tests | ✅ 111 tests verdes (backend) · 15 unit + 4 E2E (frontend) |
| README final del TP | ✅ `README.md` (estructura de `docs/README-TPL.md`) |
| Hardening / checklist de seguridad | ✅ `docs/SEGURIDAD.md` §7 verificado; deudas conocidas listadas ahí |

### 2.1 Código heredado reutilizable

El sistema **ya existe** en otra sesión y es la base a migrar:
`C:\Users\Gonzalo\Documents\Repositorios\donata-deco` (Streamlit + FastAPI + Motor).

**Al arrancar, leé ese repo.** Tiene lógica de negocio probada que hay que portar, no reinventar:

- `backend/app/models.py` — entidades de dominio y sus invariantes.
- `backend/app/routers/sales.py` — creación de venta, atomicidad de stock, pagos, cancelaciones.
- `backend/app/routers/reports.py` — agregaciones de dashboard.
- `backend/app/schemas/` — validación y reglas de negocio por entidad.
- `backend/tests/` — patrón de tests con pytest + `httpx.AsyncClient` + `ASGITransport`.
- `AGENTS.md`, `backend/AGENTS.md`, `frontend/AGENTS.md` — convenciones ya escritas.

**Portar la lógica, no el framework.** Lo que cambia: frontend Streamlit → React, y los
cambios de alcance que están en la sección 3.

---

## 3. Decisiones de alcance — NO NEGOCIABLES

Estas decisiones vinieron del usuario. **No las propongas de nuevo, no las reviertas sin
pedirlo explícitamente.**

### 3.1 Sin roles de usuario

Es un sistema de un solo tipo de usuario (el dueño del emprendimiento). **No existe `role`.**

- ❌ No crear campo `role` en el modelo `User`.
- ❌ No crear dependencias tipo `require_roles(...)`.
- ❌ No crear módulo de administración de usuarios ni pantalla de permisos.
- ❌ No crear tests de autorización por rol.
- ✅ La autorización se reduce a: *¿el request tiene un JWT válido?*
- ✅ El campo `active` **sí** existe: permite suspender el acceso de una cuenta concreta sin
  borrar su historial.

### 3.2 Producto → Proveedor obligatorio

Todo producto pertenece a **exactamente un** proveedor.

- `Product.provider_id` es **obligatorio** en alta y en edición.
- El backend valida que el `provider_id` exista en `providers` → `422` si no.
- El frontend impide guardar sin proveedor.
- Borrar un proveedor con productos asociados → `409`.
- No existe el caso "producto sin proveedor" ni siquiera como default.

### 3.3 IA 100 % local

El asistente usa un **modelo local de ~7B parámetros** (Ollama). No hay API de IA cloud.

- No agregar `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` ni similar.
- `OLLAMA_BASE_URL` apunta a `localhost:11434` (o `host.docker.internal:11434` si el backend
  corre en Docker).
- Modelo por defecto: `qwen2.5:7b-instruct` (buen seguimiento de instrucciones y tool-calling
  en español). Alternativas aceptables: `llama3.1:8b`, `mistral:7b`.
- `temperature` baja (0.1–0.2): los datos de negocio no admiten creativity.
- **Si Ollama no está disponible, el sistema debe operar con normalidad** y el chat informar
  que no está disponible. La IA es un accesorio, no un punto único de falla.

### 3.4 El asistente no toca la base de datos — actúa por MCP

Sólo puede actuar mediante **tools tipadas** que invocan la lógica de negocio ya validada. No
ejecuta SQL, ni código, ni consultas arbitrarias. Toda acción de escritura pide confirmación
humana primero.

- Las tools se exponen en un **servidor MCP propio** (`backend/app/mcp_server.py`, FastMCP,
  transporte stdio) y el agente las consume con `langchain-mcp-adapters`. Ver `docs/MCP.md` §2.0.
- Cada tool **envuelve un `service`**, nunca un repositorio directo: hereda las mismas reglas
  (stock atómico, montos enteros, saldo derivado) que la API.
- La recuperación de documentación (RAG) es local: **Chroma + embeddings HuggingFace**. Nunca
  una API cloud.
- El servidor MCP es un **subproceso del backend**, no un servicio de red: no se expone a
  Internet ni a la red del compose.

### 3.5 Doble precio minorista / mayorista

Es una decisión de negocio real, no un extra: el mismo producto tiene dos precios y el cliente
determina cuál aplica.

- `Product.price` (minorista) y `Product.price_mayorista`.
- `Client.type` ∈ `minorista | mayorista | ambos`. Un cliente `ambos` elige el precio al
  crear la orden.
- El ítem de venta guarda su `unit_price` **resuelto** en el momento de crearla, para que un
  cambio de precio futuro no altere la historia.

### 3.6 Montos en pesos enteros

`int` en ARS, **nunca `float`**. Sin decimales. Es la regla más fácil de romper y la más
característica del dominio. El único float permitido es el porcentaje de descuento.

### 3.7 Saldo siempre derivado

`saldo = total − Σ pagos`. **Nunca se persiste** como campo. Se calcula al leer. El estado de
cobranza (`sin_pago | parcial | pagada`) también se deriva.

El estado de **cumplimiento** (`pendiente | en_proceso | entregado | cancelado`) y el de
**cobranza** son **independientes**: una orden puede estar entregada y unpaid, o pagada y sin
enviar.

### 3.8 Ítems mixtos en las órdenes

Un ítem de orden referencia un producto del catálogo **o** es texto libre. En la operación
real los pedidos llegan manuscritos (*"Sumatra 100x70 agregar tira de perlas"*) y no siempre
hay producto de catálogo que los represente. Ambos tipos conviven en la misma orden.

### 3.9 Stock atómico y auditado

- Todo descuento de stock es una **única operación condicional** (`stock >= qty`).
- Si un solo ítem de una orden falla, **se revierte todo** (rollback completo, no parcial).
- **Todo** movimiento de stock —manual o automático— escribe un registro en el historial con
  cantidad con signo, stock resultante, motivo, tipo y referencia (origen).
- Cancelar o eliminar una orden **restaura** el stock; revertir una cancelación lo **vuelve a
  descontar**. Un movimiento **nunca se borra**: el "deshacer" genera un movimiento inverso.

---

## 4. Stack y comandos

| Capa | Tecnología |
|---|---|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS + TanStack Query + React Router + Zod |
| Backend | Python 3.12 + FastAPI + Pydantic v2 + Motor + PyJWT |
| BD | MongoDB Atlas (SRV) |
| IA | LangChain + `langchain-ollama` (Ollama ~7B) + **MCP** (`fastmcp` + `langchain-mcp-adapters`) + RAG (`chromadb` + embeddings HuggingFace) |
| Infra | Docker + Docker Compose |
| Tests | pytest + pytest-asyncio + httpx (backend), Vitest (frontend) |

### Comandos canónicos

```bash
docker compose up --build              # levantar backend + frontend
docker compose logs -f api             # logs del backend
docker compose run --rm api pytest     # tests del backend
curl http://localhost:8000/health      # health check
# http://localhost:5173  → aplicación web
# http://localhost:8000/docs → documentación interactiva de la API
```

### Variables de entorno (resumen)

`MONGO_URI` · `MONGO_DB` · `JWT_SECRET` · `JWT_EXPIRE_MINUTES` · `GOOGLE_CLIENT_ID` ·
`GOOGLE_CLIENT_SECRET` · `GOOGLE_REDIRECT_URI` · `CORS_ORIGINS` · `OLLAMA_BASE_URL` ·
`OLLAMA_MODEL` · `RATE_LIMIT_*`

Los secretos **sólo** por `.env`. Nunca en el repo. `.env.example` documenta cada variable.

---

## 5. Convenciones de código

- Identificadores, endpoints, colecciones, archivos y ramas en **inglés** (`snake_case`).
- Textos de UI y mensajes de error en **español**: son los usuarios.
- Endpoints REST plurales: `/clients`, `/products`, `/sales/{id}/payments`.
- Schemas Pydantic v2 con `ConfigDict(from_attributes=True)`. `_id` de Mongo → `id` (str) en la API.
- Backend organizado en capas: `routers/` (HTTP) → `services/` (negocio) → `repositories/` (Mongo).
  La lógica de negocio **nunca** vive en el router.
- Frontend organizado por *feature*, no por tipo de archivo:
  `src/features/<feature>/{components,hooks,api,types}.ts`.
- **No agregar comentarios al código** salvo pedido explícito del usuario.
- Nada de secrets en el código. Nada de `print()` en el backend: usar `logging`.
- Toda regla de negocio nueva lleva su test. Sin excepción.

---

## 6. Seguridad — checklist no negociable

Detalle completo en `docs/SEGURIDAD.md`. Mínimo obligatorio:

### Backend
- [ ] JWT Bearer en **todo** endpoint salvo `/health`, `/auth/google/*` y la documentación.
- [ ] **CORS con lista blanca explícita**. Nunca `*` con `allow_credentials=True`.
- [x] **Rate limiting** por endpoint: login (fuerte), chat, exportación, escritura, general.
- [x] Headers de seguridad: HSTS, `X-Content-Type-Options`, `X-Frame-Options`,
      `Referrer-Policy`, `Permissions-Policy`.
- [ ] Validación estricta de entrada en todos los schemas; límite de tamaño de body.
- [ ] Errores en español y **sin stack traces** hacia el cliente.
- [ ] Consultas de Mongo siempre parametrizadas por diccionario; **nunca** `eval` ni
      construcción de queries con f-strings sobre input del usuario.

### Frontend
- [ ] Guard de rutas autenticadas; nada de datos en la URL ni en el `localStorage` sin revisar.
- [ ] Interceptores para `401` (cerrar sesión) y `429` (respetar `Retry-After`).
- [ ] Validación con Zod **antes** de enviar — pero la decisión siempre la toma el backend.
- [ ] Sin `dangerouslySetInnerHTML` con contenido del usuario. Sin HTML arbitrario del LLM:
      renderizar el texto del asistente como texto o markdown sanitizado.
- [ ] CSP en producción.

### IA
- [ ] El LLM no accede a la BD: sólo tools tipadas.
- [ ] Confirmación humana antes de toda escritura.
- [x] Rate limit dedicado al chat (un 7B en CPU es un recurso caro y limitado).
- [ ] Historial de conversaciones para auditoría.

---

## 7. Cómo trabajar en este repo (proceso)

El proyecto se construye **Spec-Driven con [OpenSpec](https://github.com/Fission-AI/OpenSpec)**:
`openspec/specs/` describe el sistema tal como está construido, y todo cambio nuevo pasa por una
propuesta aprobada **antes** de escribir código.

```
explore → propose → review → apply → verify → archive
```

Los flujos viven en los skills `openspec-*` y sus comandos `/opsx-*`
(`/opsx-explore`, `/opsx-propose`, `/opsx-apply`, `/opsx-verify`, `/opsx-sync`, `/opsx-archive`).

1. **Antes de implementar un CU**, leé su sección en `docs/CASOS_DE_USO.md` y su spec en
   `openspec/specs/`. Los criterios de aceptación son el checklist de terminado.
2. **Un change por vez.** No mezcles dos propuestas en la misma rama; las tareas viven en
   `openspec/changes/<nombre>/tasks.md` y se van tachando al implementar.
3. **TDD en el backend**: test que falla → implementación → suite verde. El backend hereda el
   patrón de `donata-deco/backend/tests`.
4. **Verificá antes de dar algo por terminado**: `pytest` + typecheck + lint del frontend.
   Si algo falla, **no** digas que está terminado. Iterá.
5. **Documentá mientras avanzás**: los prompts que usaste, los intentos fallidos y por qué
   fallaron. Alimentá la bitácora de AI Engineering del README (1 pt + 3 pts de rúbrica).
6. **Commits chicos y verificables**, mensajes en español, en modo imperativo.

### Iteración con IA — lo que se evalúa

La rúbrica pide demostrar *orquestación*, no sólo código final. En cada tarea:

- **Delimitá** el contexto en el prompt (archivos, reglas de negocio, criterios de aceptación).
- **Pedí** una implementación y después una **revisión adversarial** ("¿qué se rompe acá?").
- **Iterá** hasta que los tests pasen. Los fallos son evidencia de proceso, no vergüenza:
  documentá el ciclo en `docs/AI-ENGINEERING.md`.
- Si algo no se puede resolver en 2 intentos, **cambiá de estrategia** (reformular el prompt,
  dividir la tarea, cambiar el enfoque) y dejá escrito por qué.

---

## 8. Mapa del repositorio

```
donata-ia/
├── AGENTS.md              ← estás leyendo esto
├── README.md              → se completa al final (entregable del TP)
├── opencode.json          → configuración de agentes, comandos, MCP y permisos
├── .opencode/
│   ├── agent/             → subagentes especializados
│   ├── commands/          → comandos /opsx-* de OpenSpec + /nueva-regla
│   └── skills/            → skills openspec-* y ollama-local
├── openspec/
│   ├── config.yaml        → context, rules y operations del flujo OpenSpec
│   ├── specs/             → especificaciones vivas del sistema (as-built)
│   └── changes/           → propuestas en curso y archive/
├── docs/
│   ├── CASOS_DE_USO.md    → los 10 casos de uso (fuente de verdad funcional)
│   ├── CASOS_DE_USO.pdf   → entregable para validación docente
│   ├── ARQUITECTURA.md    → decisiones técnicas y diagramas
│   ├── PLAN-IMPLEMENTACION.md → fases, tareas, estado del avance
│   ├── AI-ENGINEERING.md → bitácora de prompts, iteraciones, agentes (TP)
│   ├── SEGURIDAD.md       → modelo de amenazas y controles implementados
│   ├── MCP.md             → servidores MCP y su rol (TP)
│   └── adr/               → Architecture Decision Records
├── backend/               → FastAPI
│   ├── app/mcp_server.py  → servidor MCP `donata-mcp` (tools del asistente)
│   ├── app/services/llm/  → agente, RAG, guardrails, vector store
│   ├── knowledge/         → manual operativo (fuente del RAG)
│   └── scripts/           → ingest_kb.py, e2e_check.py
├── frontend/              → React + Vite
└── scripts/               → utilidades (incluye md2pdf.py)
```

---

## 9. Cosas que NO debo hacer sin preguntar

- Cambiar el stack, agregar una dependencia grande o cambiar la estructura de carpetas.
- Tocar los 10 casos de uso o sus criterios de aceptación (son un entregable **validado**).
- Agregar roles, permisos o multi-tenencia.
- Mandar datos del negocio a un servicio de IA externo.
- Borrar registros de stock o de órdenes.
- Hacer `git commit` o `git push` sin pedido explícito.
- Crear documentación que no me pidan (salvo los archivos de contexto de este bootstrap).

---

## 10. Primeros pasos cuando se retome el trabajo

1. Leer `docs/PLAN-IMPLEMENTACION.md` → sección de estado.
2. Confirmar con el usuario el **feedback de validación** de los casos de uso.
3. Ajustar los documentos si el docente pidió cambios.
4. Elegir el primer CU a implementar y arrancar un change con `/opsx-propose`.
