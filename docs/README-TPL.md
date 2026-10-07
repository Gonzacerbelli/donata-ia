# Donata IA

<!--
PLANTILLA del README final (entregable del TP · 1 punto de documentación).

No completar hasta el final del proyecto. Ir llenando las secciones 5 y 6 a medida que
se trabaja, alimentándose de docs/AI-ENGINEERING.md y docs/MCP.md.

Al terminar, borrar todos los comentarios HTML de este archivo.
-->

Sistema web de gestión para **DonataDeco**, emprendimiento de macramé y decoración del hogar.
Reemplaza la operatoria en planillas Excel por una aplicación unificada de ventas, stock,
pedidos, proveedores y envíos, con un asistente de IA local.

![Captura del dashboard](docs/img/dashboard.png)

---

## 1. Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 19 · TypeScript · Vite · Tailwind CSS · TanStack Query |
| Backend | FastAPI · Pydantic v2 · Motor (MongoDB asíncrono) · PyJWT |
| Base de datos | MongoDB Atlas |
| IA | LangChain + modelo local 7B (Ollama) |
| Infraestructura | Docker · Docker Compose |
| Tests | pytest · Vitest · Playwright |

---

## 2. Puesta en marcha

```bash
git clone <url>
cd donata-ia
cp .env.example .env          # completar variables (ver más abajo)
docker compose up --build
```

| Servicio | URL |
|---|---|
| Aplicación web | http://localhost:5173 |
| Documentación API | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

### Variables de entorno requeridas

| Variable | Para qué |
|---|---|
| `MONGO_URI` | Connection string de MongoDB Atlas |
| `JWT_SECRET` | Firma de los tokens. Generar: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth 2.0 (CU01) |
| `CORS_ORIGINS` | Lista blanca de orígenes del frontend |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | Asistente IA local |

### Modelo de IA

```bash
ollama pull qwen2.5:7b-instruct
ollama serve
```

Sin Ollama, **el resto del sistema funciona con normalidad**: sólo el chat queda deshabilitado.

---

## 3. Arquitectura

<!-- Diagrama en mermaid o imagen. Complementa docs/ARQUITECTURA.md -->

```
[React SPA] ──REST/JWT──▶ [FastAPI] ──▶ [MongoDB Atlas]
                              │
                              └──▶ [Ollama local 7B]
```

Decisiones técnicas y sus porqués: [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md).

---

## 4. Los 10 casos de uso

Especificación completa: [`docs/CASOS_DE_USO.md`](docs/CASOS_DE_USO.md) ·
PDF: [`docs/CASOS_DE_USO.pdf`](docs/CASOS_DE_USO.pdf)

| ID | Caso de uso | Módulos | Estado |
|---|---|---|---|
| CU01 | Autenticación OAuth 2.0 con Google | Front + Back | <!-- ✅/❌ --> |
| CU02 | Home / Dashboard con métricas y filtros por fecha | Front + Back | |
| CU03 | ABM de Productos | Front + Back | |
| CU04 | ABM de Clientes | Front + Back | |
| CU05 | ABM de Órdenes / Pedidos (con pagos) | Front + Back | |
| CU06 | ABM de Proveedores | Front + Back | |
| CU07 | Chat IA para operar el negocio en lenguaje natural | Front + Back + IA | |
| CU08 | Manejo de Stock de Productos | Front + Back | |
| CU09 | Notificaciones en plataforma | Front + Back | |
| CU10 | Exportación CSV / Excel respetando filtros de pantalla | Front + Back | |

<!-- Para cada CU: una captura y una línea de cómo se resuelve. -->

---

## 5. AI Engineering

> Sección clave de la rúbrica (3 puntos). El detalle completo está en
> [`docs/AI-ENGINEERING.md`](docs/AI-ENGINEERING.md); acá va el resumen.

### 5.1 Herramientas y configuración

| Herramienta | Rol |
|---|---|
| <!-- ... --> | |

### 5.2 Orquestación de agentes

<!-- Tabla de agentes: nombre, rol, qué tarea delega -->

### 5.3 Prompts clave

<!-- 3 o 4 prompts de texto que realmente hicieron que la implementación funcionara,
     con por qué funcionaron -->

### 5.4 Iteraciones

<!-- Qué falló, cómo se detectó, cómo se resolvió. Los fallos son evidencia de proceso. -->

### 5.5 Loops de autocorrección

<!-- TDD, revisión adversarial, evaluación del chat IA -->

---

## 6. MCP — Model Context Protocol

Detalle y configuración: [`docs/MCP.md`](docs/MCP.md). Hay **dos planos** de MCP:

**Plano A — dentro del producto.** El asistente CU07 consume sus 12 herramientas de negocio a
través de un servidor MCP **propio** (`donata-mcp`, FastMCP, stdio), levantado como subproceso y
consumido con `langchain-mcp-adapters`. Cada tool envuelve un `service`, por lo que el agente
respeta las mismas reglas que la API. Verificación E2E real:

```bash
docker compose run --rm --no-deps api python -m scripts.e2e_check
```

**Plano B — en el entorno de desarrollo.**

| Servidor | Tipo | Rol en el desarrollo |
|---|---|---|
| `context7` | externo | Documentación versionada de librerías |
| `filesystem` | externo | Acceso al sistema heredado a portar |
| `playwright` | externo | Verificación de la UI en navegador real |
| `sequential-thinking` | externo | Razonamiento estructurado para decisiones complejas |
| `github` | externo remoto | Rama + PR + merge de cada hito |

Cobertura: **1 servidor MCP propio** (arquitectura) + **5 servidores MCP** en el entorno de
desarrollo, **uno remoto**.

---

## 7. Seguridad

Modelo de amenazas y checklist: [`docs/SEGURIDAD.md`](docs/SEGURIDAD.md)

- Autenticación JWT en todos los endpoints no públicos
- Sin roles: la autorización es "¿el JWT es válido?"
- CORS con lista blanca explícita
- Rate limiting por endpoint
- Validación estricta de entrada y mensajes sin stack traces
- El asistente IA sólo puede actuar mediante tools tipadas, con confirmación humana antes de escribir
- Todo el cómputo es local: los datos del negocio no salen de la máquina

---

## 8. Estructura del repositorio

```
donata-ia/
├── backend/          FastAPI: routers, services, repositories, tests
├── frontend/         React: features, components, lib
├── docs/             Especificación, arquitectura, seguridad, bitácora
├── specs/            Especificaciones por caso de uso
├── scripts/          Utilidades
├── AGENTS.md         Contexto del proyecto para agentes de IA
└── opencode.json     Configuración de agentes, comandos y MCP
```

---

## 9. Tests

```bash
docker compose run --rm api pytest       # backend
cd frontend && npm test                  # frontend
cd frontend && npx playwright test       # E2E
```

<!-- Cobertura, qué casos borde se cubren, y qué se probó a mano. -->

---

## 10. Autores

<!-- Integrantes del equipo -->
