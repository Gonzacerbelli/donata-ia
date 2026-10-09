# Donata IA

Sistema web de gestión para **DonataDeco**, emprendimiento de macramé y decoración del hogar.
Reemplaza la operatoria en planillas Excel por una aplicación unificada de ventas, stock,
pedidos, proveedores y envíos, con un asistente de IA local.

**Trabajo Práctico Integrador** — Diplomatura en Desarrollo y Arquitectura de Agentes de IA.

---

## 1. Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 19 · TypeScript · Vite · Tailwind CSS · TanStack Query · React Router |
| Backend | FastAPI · Pydantic v2 · Motor (MongoDB asíncrono) · PyJWT |
| Base de datos | MongoDB (local en Docker o Atlas) |
| IA | LangChain + MCP (`langchain-mcp-adapters`) + modelo local 14B vía Ollama |
| Infraestructura | Docker · Docker Compose |
| Tests | pytest · Vitest · Playwright |

---

## 2. Puesta en marcha

```bash
git clone https://github.com/Gonzacerbelli/donata-ia.git
cd donata-ia
cp .env.example .env          # completar variables (ver abajo)
ollama pull qwen2.5:14b-instruct
ollama pull nomic-embed-text
docker compose up --build
```

| Servicio | URL |
|---|---|
| Aplicación web | http://localhost:5173 |
| Documentación API | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

Login local de emergencia (habilitado por `ENABLE_LOCAL_LOGIN=true`): `admin` / `cambiar-esta-clave`
— **cambiarlo en `.env`** antes de exponer el servicio.

### Datos de demostración

```bash
docker compose run --rm --no-deps api python -m scripts.seed_demo
```

Genera 4 proveedores, 15 productos de macramé, 10 clientes y ~58 órdenes repartidas en el último
año, con pagos y estados variados, para que el dashboard muestre métricas reales.

### Variables de entorno requeridas

| Variable | Para qué |
|---|---|
| `MONGO_URI` | Connection string de MongoDB |
| `JWT_SECRET` | Firma de los tokens. Generar: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth 2.0 (CU01). Opcional |
| `CORS_ORIGINS` | Lista blanca de orígenes del frontend |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | Asistente IA local |

### Modelo de IA

```bash
ollama pull qwen2.5:14b-instruct
ollama pull nomic-embed-text
ollama serve
```

Sin Ollama, **el resto del sistema funciona con normalidad**: sólo el chat queda deshabilitado
(responde `503` y la UI lo informa) y las búsquedas semánticas degradan a búsqueda por texto.

---

## 3. Arquitectura

```
[React SPA] ──REST/JWT──▶ [FastAPI] ──▶ [MongoDB]
                              │
                              ├──▶ [Servidor MCP "donata-mcp" (stdio, subproceso)]
                               │         └──▶ [Ollama local 14B]
                              └──▶ [Chroma + embeddings locales]
```

Decisiones técnicas y sus porqués: [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md).

---

## 4. Los 10 casos de uso

Especificación completa: [`docs/CASOS_DE_USO.md`](docs/CASOS_DE_USO.md) ·
PDF: [`docs/CASOS_DE_USO.pdf`](docs/CASOS_DE_USO.pdf)

| ID | Caso de uso | Módulos | Estado |
|---|---|---|---|
| CU01 | Autenticación OAuth 2.0 con Google (+ login local) | Front + Back | ✅ |
| CU02 | Home / Dashboard con métricas y filtros por fecha | Front + Back | ✅ |
| CU03 | ABM de Productos | Front + Back | ✅ |
| CU04 | ABM de Clientes | Front + Back | ✅ |
| CU05 | ABM de Órdenes / Pedidos (con pagos) | Front + Back | ✅ |
| CU06 | ABM de Proveedores | Front + Back | ✅ |
| CU07 | Chat IA para operar el negocio en lenguaje natural | Front + Back + IA | ✅ |
| CU08 | Manejo de Stock de Productos | Front + Back | ✅ |
| CU09 | Notificaciones en plataforma | Front + Back | ✅ |
| CU10 | Exportación CSV / Excel respetando filtros de pantalla | Front + Back | ✅ |

- **Dashboard:** KPIs de ventas, órdenes, cobrado y por cobrar con rango de fechas; productos más
  vendidos, stock bajo y valor de inventario. Cada KPI navega al módulo con los filtros aplicados.
- **Órdenes:** alta con ítems mixtos (catálogo + ítem libre), detalle, pagos, cambio de estado y
  baja con confirmación; el backend bloquea la baja si hay pagos.
- **Stock:** sólo se modifica desde CU08 (ajuste con motivo) o por venta; todo movimiento queda
  auditado en `stock_moves`.
- **Exportación:** los botones CSV/Excel envían exactamente los filtros activos de la pantalla.
- **Chat:** el asistente **no ejecuta escrituras por su cuenta** (ver §7).

---

## 5. AI Engineering

> Resumen. El detalle completo está en [`docs/AI-ENGINEERING.md`](docs/AI-ENGINEERING.md).

### 5.1 Herramientas y configuración

| Herramienta | Rol |
|---|---|
| `opencode` + `opencode.json` | CLI de agentes: 5 subagentes, 9 comandos, 10 skills y 6 servidores MCP |
| `.opencode/agent/` | backend · frontend · ai-engineer · reviewer · security-auditor |
| `.opencode/skills/openspec-*` | Flujos de [OpenSpec](https://github.com/Fission-AI/OpenSpec): explore, propose, apply, verify, sync, archive, update, onboard |
| `.opencode/skills/ollama-local` | Reglas para trabajar con el modelo local (guardrails, confirmación, latencia) |
| LangChain + `langchain-mcp-adapters` | Bucle de tool-calling acotado (6 pasos) sobre MCP |
| Ollama `qwen2.5:14b-instruct` | Lenguaje natural, temperatura 0 |
| `sentence-transformers/all-MiniLM-L6-v2` | Embeddings locales para RAG sobre el manual operativo |

### 5.2 Orquestación de agentes

| Agente | Rol | Delega en |
|---|---|---|
| OpenSpec (`openspec-*`) | Dirige el ciclo spec → código: propone, implementa por tareas y archiva | `/opsx-explore` · `/opsx-propose` · `/opsx-apply` · `/opsx-archive` |
| backend-engineer / frontend-engineer | Implementan y testean | `/opsx-apply` |
| ai-engineer | Ajusta prompt, tools y evaluación del modelo | chat del producto |
| reviewer · security-auditor | Revisión adversarial y checklist de seguridad | `/opsx-apply` + `/opsx-verify` |

### 5.3 Prompts clave

1. **System prompt del agente:** define idioma, "nunca inventes datos", pesos enteros y — el que
   cambió el comportamiento — *"las herramientas de escritura no están disponibles: usá
   `proponer_accion` y esperá la confirmación en pantalla"*.
2. **Prompt de investigación (hoy `/opsx-explore`):** pedir leer el legado antes de diseñar eliminó
   reinventar reglas ya probadas (stock atómico, saldo derivado).
3. **Revisión adversarial:** "buscá invariantes rotas, casos borde y errores que el test no cubre"
   hizo aparecer los fallos de fechas UTC y de tipos del formulario.

### 5.4 Iteraciones

- `formatDate` parseaba fechas sin hora como UTC y retrocedía un día al formatear en Buenos Aires
  → detectado con test, corregido con manejo determinista del patrón.
- El primer build de F6 falló por un hook mal nombrado y un `onSubmit` desalineado → se separó el
  payload del formulario del modelo de dominio (`ProductFormOutput`).
- `proponer_accion` declaraba `argumentos_json: str` y el modelo mandaba objeto → validación de
  Pydantic fallaba y la propuesta se perdía → se acepta `dict | str` y se normaliza.
- La exportación no puede ser un `<a href>` porque el token va en el header `Authorization` →
  `GET` con `responseType: "blob"` + `URL.createObjectURL`.

### 5.5 Loops de autocorrección

- **TDD:** 142 funciones de test (≈176 casos de pytest con parametrización, ruff `E/F/I/UP/B` limpio) y 45 de Vitest; las invariantes de
  negocio tienen test antes de tocar el código.
- **Evaluación del chat:** `scripts/e2e_check.py` contra Ollama real (tools MCP + RAG) y prueba
  manual del flujo de propuesta → confirmación → ejecución.
- **E2E de UI:** 9 tests de Playwright (auth, guard de rutas, historial, exportación CSV, listado → detalle).
- **Revisión adversarial y de seguridad** al cierre de cada hito, antes del merge.

---

## 6. MCP — Model Context Protocol

Detalle: [`docs/MCP.md`](docs/MCP.md). Hay **dos planos**:

**Plano A — dentro del producto.** El asistente CU07 consume **16 herramientas de negocio** a
través de un servidor MCP **propio** (`donata-mcp`, FastMCP, transporte stdio), levantado como
subproceso del agente y consumido con `langchain-mcp-adapters`. Cada tool envuelve un `service`,
así que el agente respeta exactamente las mismas reglas que la API (stock atómico, saldo derivado,
montos enteros). Verificación E2E real:

```bash
docker compose run --rm --no-deps api python -m scripts.e2e_check
```

**Plano B — en el entorno de desarrollo** (bloque `mcp` de [`opencode.json`](opencode.json)):

| Servidor | Tipo | Configuración | Rol en el desarrollo |
|---|---|---|---|
| `context7` | local (externo) | `["npx","-y","@upstash/context7-mcp"]` | Documentación versionada de librerías |
| `filesystem` | local (externo) | `["npx","-y","@modelcontextprotocol/server-filesystem", <repo heredado>, <repo actual>]` | Acceso al sistema heredado a portar |
| `playwright` | local (externo) | `["npx","-y","@playwright/mcp"]` + `BROWSER=chromium` | Verificación de la UI en navegador real |
| `sequential-thinking` | local (externo) | `["npx","-y","@modelcontextprotocol/server-sequential-thinking"]` | Razonamiento estructurado para decisiones complejas |
| `github` | **remoto** | `url: https://api.githubcopilot.com/mcp/`, header `Authorization: Bearer {env:GITHUB_PAT}` | Rama + PR + merge de cada hito |

Configuración completa y notas: [`docs/MCP.md`](docs/MCP.md) §3. Los servidores `local` corren
como subproceso vía `npx`; el único **remoto** es `github`.

Cobertura: **1 servidor MCP propio en el producto** + **5 servidores MCP en el entorno de
desarrollo (uno remoto)**.

**Autenticación del MCP `github`.** El header usa `{env:GITHUB_PAT}`, que opencode resuelve desde
el **entorno del proceso** (no desde el `.env` del proyecto): definí `GITHUB_PAT` como variable de
usuario/sistema antes de arrancar opencode. Un token **fine-grained** limitado al repo (Contents +
Pull requests) alcanza. Detalle en [`docs/MCP.md`](docs/MCP.md) §2.5 y `.env.example`.

---

## 7. Seguridad

Modelo de amenazas y checklist verificable: [`docs/SEGURIDAD.md`](docs/SEGURIDAD.md)

- Autenticación JWT en todos los endpoints no públicos; token ausente o inválido → `401`,
  usuario inactivo → `403`.
- Sin roles: la autorización es "¿el JWT es válido y la cuenta está activa?".
- CORS con lista blanca explícita (nunca `*` con credenciales) y verificado por request.
- Rate limiting propio por endpoint con `429` + `Retry-After`; la UI respeta el conteo regresivo.
- Headers de seguridad en cada respuesta (`nosniff`, `DENY`, `Referrer-Policy`, `Permissions-Policy`).
- Validación estricta de entrada; el cliente nunca ve stack traces ni nombres internos.
- **El asistente IA no tiene escrituras disponibles**: las 4 tools de escritura
  (`crear_cliente`, `crear_venta`, `registrar_pago`, `cancelar_venta`) no se le exponen; el modelo
  sólo puede *proponer* una acción y la UI pide confirmación explícita antes de ejecutarla.
- El token viaja en el header `Authorization`, nunca en la URL.
- Todo el cómputo es local (Ollama + embeddings): los datos del negocio no salen de la máquina.

---

## 8. Estructura del repositorio

```
donata-ia/
├── backend/          FastAPI: routers, services, repositories, MCP, tests
│   └── scripts/      seed_demo, e2e_check, ingest_kb
├── frontend/         React: features (auth, dashboard, providers, products,
│                     clients, orders, notifications, chat), components, e2e/
├── docs/             CASOS_DE_USO, ARQUITECTURA, PLAN, SEGURIDAD, MCP, bitácora
├── openspec/         Specs as-built y propuestas de cambios (OpenSpec)
├── scripts/          Utilidades (md2pdf)
├── AGENTS.md         Contexto del proyecto para agentes de IA
└── opencode.json     Configuración de agentes, comandos y MCP
```

---

## 9. Tests

```bash
docker compose run --rm --no-deps api sh -c "ruff check app tests; pytest -q"   # backend (~176 casos)
docker compose run --rm --no-deps api python -m scripts.e2e_check               # chat real + RAG

cd frontend && npm test              # Vitest (45)
cd frontend && npm run build         # tsc + vite
cd frontend && npm run lint          # eslint
cd frontend && npx playwright test    # E2E (9, requiere backend arriba)
```

Cobertura: invariantes de negocio (stock atómico, saldo, descuentos, paridad export/listado),
seguridad (401/403/409/422/429, CORS, headers), notificaciones, RAG y el flujo de confirmación de
acciones del chat. A mano se validó el modelo real con Ollama y la descarga de exportaciones en
navegador.

---

## 10. Documentación

| Documento | Para qué |
|---|---|
| [`docs/CASOS_DE_USO.md`](docs/CASOS_DE_USO.md) | Fuente de verdad funcional |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Capas, modelo de datos, decisiones |
| [`docs/PLAN-IMPLEMENTACION.md`](docs/PLAN-IMPLEMENTACION.md) | Fases y estado (F0–F8) |
| [`docs/SEGURIDAD.md`](docs/SEGURIDAD.md) | Modelo de amenazas y checklist verificado |
| [`docs/AI-ENGINEERING.md`](docs/AI-ENGINEERING.md) | Bitácora del proceso (entregable) |
| [`docs/MCP.md`](docs/MCP.md) | Servidores MCP (entregable) |
| [`AGENTS.md`](AGENTS.md) | Contexto del proyecto para agentes de IA |
