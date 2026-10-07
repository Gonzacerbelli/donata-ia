# Arquitectura — Donata IA

> Documento de referencia técnica. Complementa a `AGENTS.md` (que tiene las reglas) y a
> `docs/CASOS_DE_USO.md` (que tiene el qué).

---

## 1. Vista general

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        NAVEGADOR (localhost:5173)                        │
│  React 19 + TypeScript + Vite + Tailwind + TanStack Query                │
│                                                                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────┐ │
│  │ Dashboard  │ │  Productos │ │  Órdenes   │ │  Clientes  │ │ ChatIA │ │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────┬───┘ │
│                                                     NotificationBell │ │
└──────────────────────────────────────────────────────┬───────────────┼─┘
                                                       │  REST + JWT   │
                                                       ▼               │ SSE
┌──────────────────────────────────────────────────────────────────────────┐
│                      FastAPI (uvicorn, puerto 8000)                      │
│                                                                           │
│  middleware: CORS · SecurityHeaders · RateLimit · RequestID · ErrorHandler│
│                                                                           │
│  routers/     auth · providers · products · clients · sales · stock      │
│               reports · notifications · exports · ai_chat                │
│  ─────────────────────────────────────────────────────────────           │
│  services/    products · clients · sales · stock · reports · exports     │
│               notifications · auth                                       │
│  services/llm agent · tools · prompts · ollama_client                    │
│  ─────────────────────────────────────────────────────────────           │
│  repositories/  acceso a MongoDB (Motor). Toda query vive acá.           │
│  core/        config · errors · security · validation                     │
└───────────┬──────────────────────────────────────────┬───────────────────┘
            │                                          │
            ▼                                          ▼
   ┌─────────────────┐                    ┌──────────────────────────┐
   │  MongoDB Atlas  │                    │  Ollama (localhost:11434)│
   │  SRV / M0       │                    │  qwen2.5:7b-instruct     │
   └─────────────────┘                    │  LOCAL · sin internet    │
                                          └──────────────────────────┘
```

---

## 2. Capas y responsabilidad

| Capa | Responsabilidad | **Nunca** hace |
|---|---|---|
| `routers/` | HTTP: parsear, validar con el schema, delegar, responder | Reglas de negocio. Consultas a Mongo |
| `services/` | Reglas de negocio, transacciones, orquestación | Conocer HTTP (`Request`, `Response`) |
| `repositories/` | MongoDB: índices, agregaciones, filtros | Decisiones de negocio |
| `core/` | Config, errores, seguridad, utilidades transversales | Lógica de dominio |
| `services/llm/` | Agente LangChain, tools, prompts | Queries directas a Mongo |

**Por qué importa:** las tools del agente IA (CU07) llaman a los **services**, igual que los
routers. Así hay **una sola implementación** de la lógica de negocio y el chat no puede
introducir un segundo camino con reglas distintas. Es también lo que garantiza que el LLM no
toque la base de datos.

---

## 3. Modelo de datos

### 3.1 Colecciones

```
users          google_sub, email, name, picture, active, created_at, last_login_at
providers      name, contact, phone, email, cuit, notes, active
products       name, category, description, price, price_mayorista, cost,
               stock, min_stock, unit, provider_id (OBLIGATORIO), active
clients        name, phone, email, instagram, address, type, notes
sales          client_id, client_type, date, ship_by, payment_due, items[],
               subtotal, shipping_cost, discount, discount_pct, total,
               status, payments[], notes
stock_moves    product_id, product_name, quantity, stock_after, reason,
               ref_type, ref_id, created_at
notifications  user_id, key, type, severity, title, message,
               entity_type, entity_id, read, dismissed, created_at
chat_threads   thread_id, user_id, title, created_at
chat_messages  thread_id, role, content, tool_calls[], created_at
```

### 3.2 Relaciones

```
Provider 1 ────< N Product          (producto SIN proveedor es inválido)
Client   1 ────< N Sale
Product  1 ────< N SaleItem         (embebido; puede ser texto libre)
Sale     1 ────< N Payment          (embebido)
Product  1 ────< N StockMove        (auditoría inmutable)
```

**No hay joins.** MongoDB se consulta con referencias por `ObjectId` y, cuando hace falta
agregar datos de varias colecciones, con `aggregation pipeline` en el repository. Los ítems de
venta y los pagos van **embebidos** porque siempre se leen junto con su orden.

### 3.3 Campos derivados — nunca se persisten

| Dato | Fórmula |
|---|---|
| `paid` (orden) | `Σ payments.amount` |
| `balance` / `saldo` | `total − Σ payments.amount` |
| `estado de cobranza` | `sin_pago` si `balance == total` · `pagada` si `balance == 0` · `parcial` si `0 < balance < total` |
| `inventory_value` | `Σ product.cost × product.stock` |
| `total` (orden) | `subtotal − discount + shipping_cost` |

---

## 4. Reglas de negocio — referencia rápida

| # | Regla | Implementación |
|---|---|---|
| R1 | Montos en ARS enteros | `int` en Pydantic; el único `float` es `discount_pct` |
| R2 | Fechas en UTC, se muestran en Argentina | `datetime` aware UTC en Mongo; `America/Argentina/Buenos_Aires` en el frontend |
| R3 | Saldo siempre derivado | No existe el campo `balance` en la colección `sales` |
| R4 | Cobranza y cumplimiento independientes | `status` y el saldoDerived son ejes separados |
| R5 | Stock atómico | `find_one_and_update({"_id": oid, "stock": {"$gte": qty}}, {"$inc": {"stock": -qty}})` |
| R6 | Rollback total de stock | Si un ítem falla, se revierten todos los ya descontados |
| R7 | Ítems mixtos | `product_id` **o** `description`; ambos pueden convivir |
| R8 | Precio dual por ítem | Resuelto y persistido en el ítem al crear la orden |
| R9 | Cancelar restituye stock | Y revertir una cancelación lo vuelve a descontar |
| R10 | Movimiento de stock inmutable | El "deshacer" genera un movimiento inverso, nunca borra |
| R11 | Producto exige proveedor | `422` si `provider_id` no existe |
| R12 | Integridad referencial al borrar | `409` si hay referencias (cliente, producto, proveedor) |
| R13 | Export = listado | Misma query, mismos filtros, mismo orden, sin paginación |
| R14 | El LLM sólo usa tools | Sin acceso directo a datos; confirmación antes de escribir |

---

## 5. Autenticación

```
┌──────────┐        1. clic                ┌──────────────────┐
│  Browser │ ────────────────────────────► │  FastAPI         │
└────┬─────┘                              └────────┬─────────┘
     │ 2. 307 → Google                           │ 3. valida state
     ▼                                            │
┌──────────┐  4. code + state  ┌──────────────────┐│
│  Google  │ ────────────────► │  /auth/google/   ││
└──────────┘                   │  callback        ││
                               │  5. canjea code  │
                               │  6. busca/crea   │
                               │  7. firma JWT    │
                               └────────┬─────────┘
                                        │ 8. { access_token, user }
                                        ▼
                               ┌──────────────────┐
                               │  Browser         │
                               │  Authorization:  │
                               │  Bearer <token>  │  → en cada request
                               └──────────────────┘
```

- **Algoritmo:** HS256. Payload: `sub`, `email`, `iat`, `exp`.
- **Expiración:** 12 h por defecto, configurable. El frontend la conoce y cierra sesión solo.
- **`state`:** se genera en el login, se guarda en la sesión del navegador y se compara en el
  callback. Es la protección contra CSRF en el flujo OAuth.
- **Alcance de la autorización:** único. `active == false` → `403` y no se emite token.
- **Emergency:** en desarrollo se permite login local con usuario y contraseña para no quedar
  bloqueado si Google falla. **Nunca en producción.**

---

## 6. Integración con IA (CU07)

### 6.1 Elección del modelo

| Aspecto | Decisión | Motivo |
|---|---|---|
| Proveedor | **Ollama local** | Requisito: 100 % local, sin datos del negocio en la nube |
| Modelo | `qwen2.5:7b-instruct` | Mejor seguimiento de instrucciones y tool-calling en 7B |
| Temperatura | `0.1` | Los datos de negocio no admiten creativity |
| Transporte | `langchain-ollama` → HTTP a `localhost:11434` | Librarianía estándar, integra con LangChain |
| Memoria | Historial por `thread_id` | El asistente recuerda el contexto de la conversación |

### 6.2 Por qué un agente con tools y no un chatbot

Un chatbot que sólo conversa con el usuario **no puede** crear una orden. El agente usa
**function calling**: el modelo decide qué función invocar y con qué argumentos, el backend la
ejecuta y devuelve el resultado, y el modelo redacta la respuesta. Eso es lo que permite que
*"Cargale a Juan Pérez 2 Tapiz Sumatra a 45000 cada uno"* **cree la orden de verdad**.

### 6.3 Estructura de una tool

Cada tool es una función con argumentos tipados:

```python
def crear_orden(
    cliente_id: str,
    items: list[ItemOrden],
    client_type: Literal["minorista", "mayorista"] = "minorista",
    shipping_cost: int = 0,
    discount_pct: float = 0.0,
    notas: str | None = None,
) -> dict:
    ...
```

- PyDantic valida los argumentos **antes** de que la función corra.
- La tool llama al **service**, nunca a Mongo directamente.
- Devuelve un `dict` serializable, no un objeto de dominio.
- El LLM nunca ve excepciones: el service captura el error y lo devuelve como
  `{"ok": False, "error": "Stock insuficiente para Tapiz Sumatra (disponible: 3)"}` para que el
  modelo lo traduzca a lenguaje natural.

### 6.4 System prompt

Estructurado en secciones explícitas (rol → contexto → reglas duras → formato → ejemplos). Un
7B necesita estructura explícita; un prompt largo y difuso produce comportamiento errático.
El texto exacto vive en `backend/app/services/llm/prompts.py` versionado, y su evolución se
documenta en `docs/AI-ENGINEERING.md`.

Las 10 reglas duras están en `docs/CASOS_DE_USO.md` §7.3. En resumen: no inventar datos ni IDs,
confirmar antes de escribir, no ejecutar operaciones destructivas sin confirmación, montos en
pesos enteros, preguntar cuando falten datos, preguntar ante ambigüedad.

### 6.5 Degradación

```
Ollama caído  →  GET /health reporta degraded
              →  POST /chat devuelve 503 con mensaje claro
              →  la UI informa "el asistente no está disponible"
              →  TODO EL RESTO DEL SISTEMA SIGUE OPERANDO
```

La IA es un accesorio del sistema de gestión, nunca un punto único de falla. Esto es
deliberado y está en los criterios de aceptación de CU07.

### 6.6 Capa MCP — cómo el agente obtiene sus tools

Las herramientas del asistente **no** son funciones sueltas dentro del agente: se exponen en un
**servidor MCP propio** (`backend/app/mcp_server.py`, FastMCP, transporte **stdio**) y el agente
las descubre y ejecuta con `MultiServerMCPClient` (`langchain-mcp-adapters`).

```
POST /chat (router)
   └─ services/llm/assistant.py      guardrails + historial + validación de salida
        └─ services/llm/agent.py     bucle de tool-calling (ChatOllama)
             └─ MultiServerMCPClient (stdio)
                  └─ mcp_server.py   donata-mcp — 12 tools en español
                       └─ services/*  reglas de negocio (stock, ventas, clientes, reportes)
                              └─ repositories/*  →  MongoDB
   └─ services/llm/rag.py           consultar_documentacion → Chroma (embeddings locales)
```

Decisiones y porqués:

| Decisión | Motivo |
|---|---|
| Servidor MCP **propio** en vez de tools inline | Desacopla el negocio del agente y hace que las tools sean testeables por stdio, de forma aislada |
| Transporte **stdio** (subproceso), no HTTP | No expone el negocio a la red; el único cliente es el backend |
| Cada tool envuelve un **service**, no un repo | Hereda las mismas invariantes que la API (stock atómico, montos enteros, saldo derivado) |
| Entorno explícito al subproceso (`_server_env`) | El subproceso no hereda el `.env` del compose; sin esto, las tools fallan por conexión |
| RAG en **colección separada** del catálogo | El manual es estable; el catálogo cambia y se reindexa aparte |

Detalle de las herramientas y su mapeo a los servicios: `docs/MCP.md` §2.0.

---

## 7. Seguridad

Detalle completo en `docs/SEGURIDAD.md`. Resumen de la postura:

| Capa | Decisión |
|---|---|
| Autenticación | JWT Bearer en todo endpoint no público |
| Autorización | Sin roles. Sólo "¿tenés JWT válido?" |
| CORS | Lista blanca explícita desde `CORS_ORIGINS`. Nunca comodín con credenciales |
| Rate limit | Por endpoint: login (10/min), chat (20/min), export (10/min), escritura (60/min), global (120/min) |
| Headers | HSTS, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` |
| Validación | Pydantic estricto en backend (decide) + Zod en frontend (UX) |
| Errores | Handler global: mensaje en español, **nunca** stack trace al cliente; el detalle va al log |
| Body | Límite de tamaño configurables |
| Frontend | Guards de ruta, interceptores `401`/`429`, sin HTML arbitrario, CSP en producción |
| IA | Tools tipadas · confirmación antes de escribir · rate limit dedicado · sin salida de datos |

---

## 8. Decisiones técnicas y sus porqués

| Decisión | Alternativa descartada | Motivo |
|---|---|---|
| MongoDB | PostgreSQL + Prisma | El sistema ya funciona con Mongo y hay lógica probada para portar. Atlas es pedido del TP |
| Motor (async) | PyMongo síncrono | FastAPI es async; PyMongo bloquearía el event loop |
| Sin ORM, repositories con diccionarios | Beanie / MongoEngine | El control explícito de las queries atómicas de stock es crítico; un ORM lo esconde |
| LangChain | SDK directo del modelo | Requisito explícito del TP; además aporta la abstracción de tools |
| Ollama local | API cloud | Requisito del usuario: los datos del negocio no salen de la máquina |
| Tailwind + shadcn | Ant Design / MUI | Bundle chico, control total del tema, sin dependencia pesada |
| TanStack Query | Redux | El estado del servidor (cache, revalidación, mutaciones) es exactamente lo que resuelve |
| Sin roles | RBAC completo | El usuario lo decidió: es un usuario único |

---

## 9. Puntos de extensión

Dónde tocar para agregar funcionalidad sin romper lo existente:

| Quiero… | Tocar |
|---|---|
| Un caso de uso nuevo | `routers/` + `services/` + `repositories/` + `features/<nombre>/` + una sección en `docs/CASOS_DE_USO.md` |
| Un campo nuevo en una entidad | Modelo → schema → repository → service → router → schema del frontend → componente |
| Un tipo de notificación nuevo | Regla en `services/notifications.py` + tipo en el catálogo de `docs/CASOS_DE_USO.md` §9.1 |
| Una tool nueva del chat IA | Tool en `services/llm/tools.py` + descripción en el system prompt + test |
| Cambiar el modelo de IA | `OLLAMA_MODEL` en `.env`. **Probar el tool-calling antes**: no todos los 7B se comportan igual |
| Cambiar la política de rate limit | `core/security.py`, un valor por endpoint desde settings |
