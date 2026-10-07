# AGENTS.md — Backend Donata IA

> Reglas específicas del backend. **Leé también `AGENTS.md` de la raíz**: eso no se repite acá.

---

## Stack

Python 3.12 · FastAPI · Pydantic v2 · Motor (MongoDB async) · PyJWT · python-multipart ·
LangChain + langchain-ollama · **fastmcp + langchain-mcp-adapters** · **chromadb + embeddings
HuggingFace** · openpyxl · slowapi · pytest · httpx

## Estructura

```
backend/
├── app/
│   ├── main.py            app, lifespan, middlewares, handler de errores
│   ├── config.py          pydantic-settings. Lee .env y falla rápido si falta algo
│   ├── db.py              AsyncIOMotorClient, índices, ping
│   ├── dependencies.py    get_current_user
│   ├── core/
│   │   ├── errors.py      excepciones de dominio + handler
│   │   ├── security.py    rate limit, headers, CORS
│   │   └── validation.py  validadores reutilizables
│   ├── models/            modelos de dominio (Pydantic)
│   ├── schemas/           request / response por dominio
│   ├── repositories/      acceso a Mongo. Toda query vive acá
│   ├── services/          reglas de negocio
│   │   └── llm/           guardrails, vector_store, rag, agent, assistant
│   ├── routers/           HTTP
│   ├── mcp_server.py      servidor MCP donata-mcp (tools de negocio)
│   └── middleware/        rate limit, request id, context
├── knowledge/             manual operativo (fuente del RAG)
├── scripts/               ingest_kb.py, e2e_check.py
├── tests/
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

## Capa IA y MCP

El asistente (CU07) vive en `services/llm/` y `mcp_server.py`. Reglas:

| Pieza | Archivo | Regla |
|---|---|---|
| Guardrails | `services/llm/guardrails.py` | Filtra tema/injección **antes** de llamar al modelo y valida la salida |
| Vector store | `services/llm/vector_store.py` | Colecciones Chroma `donata_kb` y `donata_products`; nombres ≥ 3 chars |
| RAG | `services/llm/rag.py` | Cadena LCEL; `get_llm()` es la única fábrica de `ChatOllama` |
| Agente | `services/llm/agent.py` | Tool-calling sobre MCP con `MultiServerMCPClient` |
| Orquestador | `services/llm/assistant.py` | Guardrails + historial + agente + persistencia de `tool_calls` |
| Servidor MCP | `mcp_server.py` | FastMCP stdio; **cada tool envuelve un service**, nunca un repo directo |

- El servidor MCP corre como **subproceso** del backend (stdio), no como servicio de red.
- Al lanzarlo hay que pasarle el entorno explícito (`MONGO_URI`, `CHROMA_DIR`, `OLLAMA_BASE_URL`):
  el subproceso no hereda el `.env` del compose. Ver `agent._server_env()`.
- Todo acceso bloqueante a Chroma/embeddings va por `to_thread` para no bloquear el event loop.
- Endpoint del chat: `POST /chat` (autenticado). **Ollama caído → `503`**, el resto del sistema
  sigue operando.
- E2E real: `docker compose run --rm --no-deps api python -m scripts.e2e_check`.

## Capas

| Capa | Hace | **Nunca** |
|---|---|---|
| `routers/` | Parseo, validación con schema, delegar, responder | Reglas de negocio. Queries a Mongo |
| `services/` | Reglas de negocio, transacciones, orquestación | Conceptos de HTTP |
| `repositories/` | Queries, índices, agregaciones | Decisiones de negocio |
| `models/` | Forma del dominio e invariantes | Lógica de aplicación |

**La regla que más se rompe:** meter la lógica en el router porque "es más rápido". Después
no se puede testear sin levantar la app, y el chat IA (que llama a services, no a routers)
no la puede reutilizar.

## Convenciones

- Nombres de archivo, funciones, endpoints, colecciones y variables en **inglés** `snake_case`.
- Mensajes de error y textos de negocio en **español**.
- **Sin comentarios en el código**, salvo pedido explícito.
- `logging.getLogger(__name__)`, nunca `print`.
- `201` crear · `204` borrar · `200` resto. `400` error de negocio · `401` sin sesión ·
  `403` sin permiso · `404` no existe · `409` conflicto de integridad · `422` validación ·
  `429` rate limit · `503` dependencia caída.
- `PATCH` = merge parcial con `model_dump(exclude_unset=True)`.
- `_id` de Mongo → `id` (str) en la API. `ConfigDict(from_attributes=True)`.
- **Sin roles.** `role` no existe.

## Reglas de negocio — checklist

- [ ] Montos en `int` ARS. **Nunca `float`** (excepto `discount_pct`).
- [ ] El **saldo es derivado**: `total − Σ payments`. No existe el campo en el documento.
- [ ] El **estado de cobranza** es derivado del saldo. El de cumplimiento es `status`.
- [ ] **Stock atómico**: `find_one_and_update` con filtro `{"stock": {"$gte": qty}}` y `$inc`.
      Nunca leer → validar en Python → escribir.
- [ ] **Rollback total**: si un ítem de la orden falla, se revierten todos los ya descontados.
- [ ] **Todo movimiento de stock** escribe su registro: cantidad con signo, `stock_after`,
      `reason`, `ref_type`, `ref_id`, `created_at`.
- [ ] Cancelar restituye stock. Revertir una cancelación lo vuelve a descontar.
- [ ] Un movimiento de stock **nunca se borra**. El deshacer genera uno inverso.
- [ ] `Product.provider_id` **obligatorio** y validado contra `providers` → `422`.
- [ ] Los ítems de orden soportan producto **y** texto libre, en la misma orden.
- [ ] El precio dual se resuelve por tipo de cliente y **se persiste en el ítem**.
- [ ] Fechas: `datetime` **aware UTC** en Mongo.
- [ ] Borrar con referencias → `409`, nunca borrado en cascada.
- [ ] Export: **misma query** que el listado, mismos filtros, mismo orden, sin paginación.

## Seguridad — checklist

- [ ] `get_current_user` en todo endpoint salvo `/health`, `/auth/google/*` y docs.
- [ ] CORS desde `CORS_ORIGINS`. Nunca `*` con `allow_credentials=True`.
- [ ] Rate limit: auth 10/min · chat 20/min · export 10/min · escritura 60/min · global 120/min.
- [ ] Headers: HSTS (prod), `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
      `Permissions-Policy`.
- [ ] Validación estricta: rangos con `Field(ge=0, le=...)`, `max_length`, `EmailStr`.
- [ ] Queries como **diccionarios literales**. Nunca f-string sobre input del usuario.
- [ ] `$regex` con input del usuario → `re.escape()`.
- [ ] ObjectId inválido en el path → `404`, no `500`.
- [ ] Handler global: mensaje en español al cliente, detalle al log con `request_id`.
- [ ] Límite de tamaño de body.
- [ ] Secretos sólo por `.env`. Ningún valor por defecto hardcodeado.

## Tests

**TDD: test que falla → implementación → suite verde.** Un test que nunca falló no prueba nada.

```bash
docker compose run --rm api pytest              # todo
docker compose run --rm api pytest -k stock     # por palabra clave
```

- Base de datos **de test separada** (`MONGO_DB_TEST`), limpiada por fixture.
- Cliente `httpx.AsyncClient` con `ASGITransport` (no levantar uvicorn).
- Cada regla de negocio de esta lista tiene al menos un test.
- Cada caso borde de `docs/CASOS_DE_USO.md` tiene su test.
- Portá los tests de `../../donata-deco/backend/tests/` cuando exista la lógica equivalente.

## Comandos

```bash
docker compose up --build                  # API en 8000
docker compose logs -f api
docker compose run --rm api pytest
docker compose run --rm --no-deps api sh -c "ruff format app scripts tests; ruff check app scripts tests"
docker compose run --rm --no-deps api python -m scripts.e2e_check   # E2E real con Ollama
uvicorn app.main:app --reload              # sin docker
ruff check app && ruff format app
```

## Orden de implementación

1. `config` → `db` → `main` con middlewares → modelos → `dependencies` → routers.
2. El servicio de stock **antes** que el de órdenes (las órdenes lo usan).
3. Reports, notifications, exports, y recién al final el chat IA (es lo más difícil de
   verificar y el único que puede fallar sin romper el resto).
