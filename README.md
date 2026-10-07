# Donata IA

Sistema web de gestión para **DonataDeco**, emprendimiento de macramé y decoración del hogar.
React + FastAPI + MongoDB Atlas + Docker, con asistente de IA local (LangChain + Ollama 7B).

**Trabajo Práctico Integrador** — Diplomatura en Desarrollo y Arquitectura de Agentes de IA.

---

## 📌 Estado del proyecto

| Fase | Estado |
|---|---|
| Especificación de los 10 casos de uso | ✅ Completada |
| Validación docente | ⏳ En espera |
| Implementación | ⬜ Pendiente |

## 📄 Documentos

| Documento | Para qué |
|---|---|
| **[`docs/CASOS_DE_USO.md`](docs/CASOS_DE_USO.md)** | Los 10 casos de uso con sus criterios de aceptación. **Fuente de verdad funcional** |
| **[`docs/CASOS_DE_USO.pdf`](docs/CASOS_DE_USO.pdf)** | Entregable para validar con el docente |
| [`AGENTS.md`](AGENTS.md) | **Contexto del proyecto para agentes de IA.** Leelo primero |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Capas, modelo de datos, decisiones técnicas |
| [`docs/PLAN-IMPLEMENTACION.md`](docs/PLAN-IMPLEMENTACION.md) | Fases, tareas y estado del avance |
| [`docs/SEGURIDAD.md`](docs/SEGURIDAD.md) | Modelo de amenazas y checklist verificable |
| [`docs/AI-ENGINEERING.md`](docs/AI-ENGINEERING.md) | Bitácora del proceso (entregable del TP) |
| [`docs/MCP.md`](docs/MCP.md) | Servidores MCP y su rol (entregable del TP) |
| [`docs/README-TPL.md`](docs/README-TPL.md) | Plantilla del README final (entregable del TP) |
| [`specs/`](specs/) | Especificaciones de implementación por caso de uso |
| [`docs/adr/`](docs/adr/) | Architecture Decision Records |

## 🤖 Trabajando con IA en este repo

El proyecto está configurado para **Spec-Driven Development** con agentes de IA.

| Pieza | Ubicación | Qué hace |
|---|---|---|
| Contexto del proyecto | `AGENTS.md`, `backend/AGENTS.md`, `frontend/AGENTS.md` | Se cargan en cada sesión: las decisiones persisten |
| Configuración | `opencode.json` | Agentes, permisos y servidores MCP |
| Agentes especializados | `.opencode/agent/` | 8 agentes: research, design, tasks, backend, frontend, IA, review, seguridad |
| Comandos | `.opencode/command/` | `/sdd-research` · `/sdd-design` · `/sdd-implement` · `/nueva-regla` |
| Skills | `.opencode/skills/` | `sdd-openspec` (flujo de trabajo) · `ollama-local` (asistente IA) |

**Flujo de trabajo:**

```
/sdd-research  →  /sdd-design  →  /sdd-implement
   contexto         diseño          TDD + revisión adversarial
```

> `opencode.json` se lee **una vez al arrancar**. Después de modificarlo hay que reiniciar
> opencode para que los cambios tengan efecto.

## 🧱 Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 19 · TypeScript · Vite · Tailwind CSS · TanStack Query |
| Backend | FastAPI · Pydantic v2 · Motor · PyJWT |
| Base de datos | MongoDB Atlas |
| IA | LangChain + `qwen2.5:7b-instruct` vía Ollama (**local**) |
| Infraestructura | Docker · Docker Compose |
| Tests | pytest · Vitest · Playwright |

## 🔑 Reglas del proyecto

1. **Sin roles de usuario.** Es un sistema de un solo tipo de usuario.
2. **Producto siempre con proveedor** (`provider_id` obligatorio).
3. **IA 100 % local.** Los datos del negocio no salen de la máquina.
4. **El asistente sólo usa tools tipadas.** Nunca accede a la base de datos.
5. **Montos en enteros ARS.** El único `float` es el porcentaje de descuento.
6. **El saldo siempre se deriva** de los pagos. Nunca se persiste.
7. **El stock es atómico y auditado.** Todo movimiento queda registrado.
8. **Sin comentarios en el código**, salvo pedido explícito.

El detalle y el porqué de cada una: [`AGENTS.md`](AGENTS.md) §3.

## 🚀 Puesta en marcha

```bash
cp .env.example .env      # completar variables
ollama pull qwen2.5:7b-instruct
docker compose up --build
```

| Servicio | URL |
|---|---|
| Aplicación | http://localhost:5173 |
| Docs de la API | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

## 🛠 Utilidades

```bash
# Regenerar el PDF de casos de uso tras editar el Markdown
python scripts/md2pdf.py docs/CASOS_DE_USO.md docs/CASOS_DE_USO.pdf
```
