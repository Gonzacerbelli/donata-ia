# Arquitectura - Donata IA

> Documento de referencia t�cnica. Complementa a `AGENTS.md` (que tiene las reglas) y a
> `docs/CASOS_DE_USO.md` (que tiene el qu�).

---

## 1. Vista general

```
????????????????????????????????????????????????????????????????????????????
?                        NAVEGADOR (localhost:5173)                        ?
?  React 19 + TypeScript + Vite + Tailwind + TanStack Query                ?
?                                                                           ?
?  ?????????????? ?????????????? ?????????????? ?????????????? ?????????? ?
?  ? Dashboard  ? ?  Productos ? ?  �rdenes   ? ?  Clientes  ? ? ChatIA ? ?
?  ?????????????? ?????????????? ?????????????? ?????????????? ?????????? ?
?                                                     NotificationBell ? ?
??????????????????????????????????????????????????????????????????????????
                                                       ?  REST + JWT   ?
                                                       ?               ? SSE
????????????????????????????????????????????????????????????????????????????
?                      FastAPI (uvicorn, puerto 8000)                      ?
?                                                                           ?
?  middleware: CORS � SecurityHeaders � RateLimit � RequestID � ErrorHandler?
?                                                                           ?
?  routers/     auth � providers � products � clients � sales � stock      ?
?               reports � notifications � exports � ai_chat                ?
?  ?????????????????????????????????????????????????????????????           ?
?  services/    products � clients � sales � stock � reports � exports     ?
?               notifications � auth                                       ?
?  services/llm agent � tools � prompts � ollama_client                    ?
?  ?????????????????????????????????????????????????????????????           ?
?  repositories/  acceso a MongoDB (Motor). Toda query vive ac�.           ?
?  core/        config � errors � security � validation                     ?
????????????????????????????????????????????????????????????????????????????
            ?                                          ?
            ?                                          ?
   ???????????????????                    ????????????????????????????
   ?  MongoDB Atlas  ?                    ?  Ollama (localhost:11434)?
   ?  SRV / M0       ?                    ?  qwen2.5:7b-instruct     ?
   ???????????????????                    ?  LOCAL � sin internet    ?
                                          ????????????????????????????
```

---

## 2. Capas y responsabilidad

| Capa | Responsabilidad | **Nunca** hace |
|---|---|---|
| `routers/` | HTTP: parsear, validar con el schema, delegar, responder | Reglas de negocio. Consultas a Mongo |
| `services/` | Reglas de negocio, transacciones, orquestaci�n | Conocer HTTP (`Request`, `Response`) |
| `repositories/` | MongoDB: �ndices, agregaciones, filtros | Decisiones de negocio |
| `core/` | Config, errores, seguridad, utilidades transversales | L�gica de dominio |
| `services/llm/` | Agente LangChain, tools, prompts | Queries directas a Mongo |

**Por qu� importa:** las tools del agente IA (CU07) llaman a los **services**, igual que los
routers. As� hay **una sola implementaci�n** de la l�gica de negocio y el chat no puede
introducir un segundo camino con reglas distintas. Es tambi�n lo que garantiza que el LLM no
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
work_items     sale_id (�nico), status, priority, assigned_to, comments[], created_at, updated_at
```

### 3.2 Relaciones

```
Provider 1 ????< N Product          (producto SIN proveedor es inv�lido)
Client   1 ????< N Sale
Product  1 ????< N SaleItem         (embebido; puede ser texto libre)
Sale     1 ????< N Payment          (embebido)
Product  1 ????< N StockMove        (auditor�a inmutable)
Sale     1 ???? 1 WorkItem          (eje de trabajo; se crea por upsert)
```

**No hay joins.** MongoDB se consulta con referencias por `ObjectId` y, cuando hace falta
agregar datos de varias colecciones, con `aggregation pipeline` en el repository. Los �tems de
venta y los pagos van **embebidos** porque siempre se leen junto con su orden.

### 3.3 Campos derivados - nunca se persisten

| Dato | F�rmula |
|---|---|
| `paid` (orden) | `? payments.amount` |
| `balance` / `saldo` | `total ? ? payments.amount` |
| `estado de cobranza` | `sin_pago` si `balance == total` � `pagada` si `balance == 0` � `parcial` si `0 < balance < total` |
| `inventory_value` | `? product.cost � product.stock` |
| `total` (orden) | `subtotal ? discount + shipping_cost` |

---

## 4. Reglas de negocio - referencia r�pida

| # | Regla | Implementaci�n |
|---|---|---|
| R1 | Montos en ARS enteros | `int` en Pydantic; el �nico `float` es `discount_pct` |
| R2 | Fechas en UTC, se muestran en Argentina | `datetime` aware UTC en Mongo; `America/Argentina/Buenos_Aires` en el frontend |
| R3 | Saldo siempre derivado | No existe el campo `balance` en la colecci�n `sales` |
| R4 | Cobranza y cumplimiento independientes | `status` y el saldoDerived son ejes separados |
| R5 | Stock at�mico | `find_one_and_update({"_id": oid, "stock": {"$gte": qty}}, {"$inc": {"stock": -qty}})` |
| R6 | Rollback total de stock | Si un �tem falla, se revierten todos los ya descontados |
| R7 | �tems mixtos | `product_id` **o** `description`; ambos pueden convivir |
| R8 | Precio dual por �tem | Resuelto y persistido en el �tem al crear la orden |
| R9 | Cancelar restituye stock | Y revertir una cancelaci�n lo vuelve a descontar |
| R10 | Movimiento de stock inmutable | El "deshacer" genera un movimiento inverso, nunca borra |
| R11 | Producto exige proveedor | `422` si `provider_id` no existe |
| R12 | Integridad referencial al borrar | `409` si hay referencias (cliente, producto, proveedor) |
| R13 | Export = listado | Misma query, mismos filtros, mismo orden, sin paginaci�n |
| R14 | El LLM s�lo usa tools | Sin acceso directo a datos; confirmaci�n antes de escribir |
| R15 | El trabajo es un eje independiente | Estado de trabajo, prioridad, asignaci�n y comentarios viven en `work_items`; cambiarlos no toca `status`, pagos ni stock. Sincronizaci�n **unidireccional** con el cumplimiento: al marcar la orden `entregado` la tarjeta pasa a `terminado`; al salir de `entregado` vuelve a `pendiente`. Marcar una tarjeta `terminado` jam�s entrega la orden. Tablero: s�lo �rdenes no `entregado`/`cancelado`; tarjetas de entregadas/canceladas congeladas (`404`) |

---

## 5. Autenticaci�n

```
????????????        1. clic                ????????????????????
?  Browser ? ????????????????????????????? ?  FastAPI         ?
????????????                              ????????????????????
     ? 2. 307 ? Google                           ? 3. valida state
     ?                                            ?
????????????  4. code + state  ?????????????????????
?  Google  ? ????????????????? ?  /auth/google/   ??
????????????                   ?  callback        ??
                               ?  5. canjea code  ?
                               ?  6. busca/crea   ?
                               ?  7. firma JWT    ?
                               ????????????????????
                                        ? 8. { access_token, user }
                                        ?
                               ????????????????????
                               ?  Browser         ?
                               ?  Authorization:  ?
                               ?  Bearer <token>  ?  ? en cada request
                               ????????????????????
```

- **Algoritmo:** HS256. Payload: `sub`, `email`, `iat`, `exp`.
- **Expiraci�n:** 12 h por defecto, configurable. El frontend la conoce y cierra sesi�n solo.
- **`state`:** se genera en el login, se guarda en la sesi�n del navegador y se compara en el
  callback. Es la protecci�n contra CSRF en el flujo OAuth.
- **Alcance de la autorizaci�n:** �nico. `active == false` ? `403` y no se emite token.
- **Emergency:** en desarrollo se permite login local con usuario y contrase�a para no quedar
  bloqueado si Google falla. **Nunca en producci�n.**

---

## 6. Integraci�n con IA (CU07)

### 6.1 Elecci�n del modelo

| Aspecto | Decisi�n | Motivo |
|---|---|---|
| Proveedor | **Ollama local** | Requisito: 100 % local, sin datos del negocio en la nube |
| Modelo | `qwen2.5:7b-instruct` | Mejor seguimiento de instrucciones y tool-calling en 7B |
| Temperatura | `0.1` | Los datos de negocio no admiten creativity |
| Transporte | `langchain-ollama` ? HTTP a `localhost:11434` | Librarian�a est�ndar, integra con LangChain |
| Memoria | Historial por `thread_id` | El asistente recuerda el contexto de la conversaci�n |

### 6.2 Por qu� un agente con tools y no un chatbot

Un chatbot que s�lo conversa con el usuario **no puede** crear una orden. El agente usa
**function calling**: el modelo decide qu� funci�n invocar y con qu� argumentos, el backend la
ejecuta y devuelve el resultado, y el modelo redacta la respuesta. Eso es lo que permite que
*"Cargale a Juan P�rez 2 Tapiz Sumatra a 45000 cada uno"* **cree la orden de verdad**.

### 6.3 Estructura de una tool

Cada tool es una funci�n con argumentos tipados:

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

- PyDantic valida los argumentos **antes** de que la funci�n corra.
- La tool llama al **service**, nunca a Mongo directamente.
- Devuelve un `dict` serializable, no un objeto de dominio.
- El LLM nunca ve excepciones: el service captura el error y lo devuelve como
  `{"ok": False, "error": "Stock insuficiente para Tapiz Sumatra (disponible: 3)"}` para que el
  modelo lo traduzca a lenguaje natural.

### 6.4 System prompt

Estructurado en secciones expl�citas (rol ? contexto ? reglas duras ? formato ? ejemplos). Un
7B necesita estructura expl�cita; un prompt largo y difuso produce comportamiento err�tico.
El texto exacto vive en `backend/app/services/llm/prompts.py` versionado, y su evoluci�n se
documenta en `docs/AI-ENGINEERING.md`.

Las 10 reglas duras est�n en `docs/CASOS_DE_USO.md` �7.3. En resumen: no inventar datos ni IDs,
confirmar antes de escribir, no ejecutar operaciones destructivas sin confirmaci�n, montos en
pesos enteros, preguntar cuando falten datos, preguntar ante ambig�edad.

### 6.5 Degradaci�n

```
Ollama ca�do  ?  GET /health reporta degraded
              ?  POST /chat devuelve 503 con mensaje claro
              ?  la UI informa "el asistente no est� disponible"
              ?  TODO EL RESTO DEL SISTEMA SIGUE OPERANDO
```

La IA es un accesorio del sistema de gesti�n, nunca un punto �nico de falla. Esto es
deliberado y est� en los criterios de aceptaci�n de CU07.

### 6.6 Capa MCP - c�mo el agente obtiene sus tools

Las herramientas del asistente **no** son funciones sueltas dentro del agente: se exponen en un
**servidor MCP propio** (`backend/app/mcp_server.py`, FastMCP, transporte **stdio**) y el agente
las descubre y ejecuta con `MultiServerMCPClient` (`langchain-mcp-adapters`).

```
POST /chat (router)
   ?? services/llm/assistant.py      guardrails + historial + validaci�n de salida
        ?? services/llm/agent.py     bucle de tool-calling (ChatOllama)
             ?? MultiServerMCPClient (stdio)
                  ?? mcp_server.py   donata-mcp - 16 tools en espa�ol
                       ?? services/*  reglas de negocio (stock, ventas, clientes, reportes)
                              ?? repositories/*  ?  MongoDB
   ?? services/llm/rag.py           consultar_documentacion ? Chroma (embeddings locales)
```

Decisiones y porqu�s:

| Decisi�n | Motivo |
|---|---|
| Servidor MCP **propio** en vez de tools inline | Desacopla el negocio del agente y hace que las tools sean testeables por stdio, de forma aislada |
| Transporte **stdio** (subproceso), no HTTP | No expone el negocio a la red; el �nico cliente es el backend |
| Cada tool envuelve un **service**, no un repo | Hereda las mismas invariantes que la API (stock at�mico, montos enteros, saldo derivado) |
| Entorno expl�cito al subproceso (`_server_env`) | El subproceso no hereda el `.env` del compose; sin esto, las tools fallan por conexi�n |
| RAG en **colecci�n separada** del cat�logo | El manual es estable; el cat�logo cambia y se reindexa aparte |

Detalle de las herramientas y su mapeo a los servicios: `docs/MCP.md` �2.0.

---

## 7. Seguridad

Detalle completo en `docs/SEGURIDAD.md`. Resumen de la postura:

| Capa | Decisi�n |
|---|---|
| Autenticaci�n | JWT Bearer en todo endpoint no p�blico |
| Autorizaci�n | Sin roles. S�lo "�ten�s JWT v�lido?" |
| CORS | Lista blanca expl�cita desde `CORS_ORIGINS`. Nunca comod�n con credenciales |
| Rate limit | Por endpoint: login (10/min), chat (20/min), export (10/min), escritura (60/min), global (120/min) |
| Headers | HSTS, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` |
| Validaci�n | Pydantic estricto en backend (decide) + Zod en frontend (UX) |
| Errores | Handler global: mensaje en espa�ol, **nunca** stack trace al cliente; el detalle va al log |
| Body | L�mite de tama�o configurables |
| Frontend | Guards de ruta, interceptores `401`/`429`, sin HTML arbitrario, CSP en producci�n |
| IA | Tools tipadas � confirmaci�n antes de escribir � rate limit dedicado � sin salida de datos |

---

## 8. Decisiones t�cnicas y sus porqu�s

| Decisi�n | Alternativa descartada | Motivo |
|---|---|---|
| MongoDB | PostgreSQL + Prisma | El sistema ya funciona con Mongo y hay l�gica probada para portar. Atlas es pedido del TP |
| Motor (async) | PyMongo s�ncrono | FastAPI es async; PyMongo bloquear�a el event loop |
| Sin ORM, repositories con diccionarios | Beanie / MongoEngine | El control expl�cito de las queries at�micas de stock es cr�tico; un ORM lo esconde |
| LangChain | SDK directo del modelo | Requisito expl�cito del TP; adem�s aporta la abstracci�n de tools |
| Ollama local | API cloud | Requisito del usuario: los datos del negocio no salen de la m�quina |
| Tailwind + shadcn | Ant Design / MUI | Bundle chico, control total del tema, sin dependencia pesada |
| TanStack Query | Redux | El estado del servidor (cache, revalidaci�n, mutaciones) es exactamente lo que resuelve |
| Sin roles | RBAC completo | El usuario lo decidi�: es un usuario �nico |

---

## 9. Puntos de extensi�n

D�nde tocar para agregar funcionalidad sin romper lo existente:

| Quiero. | Tocar |
|---|---|
| Un caso de uso nuevo | `routers/` + `services/` + `repositories/` + `features/<nombre>/` + una secci�n en `docs/CASOS_DE_USO.md` |
| Un campo nuevo en una entidad | Modelo ? schema ? repository ? service ? router ? schema del frontend ? componente |
| Un tipo de notificaci�n nuevo | Regla en `services/notifications.py` + tipo en el cat�logo de `docs/CASOS_DE_USO.md` �9.1 |
| Una tool nueva del chat IA | Tool en `services/llm/tools.py` + descripci�n en el system prompt + test |
| Cambiar el modelo de IA | `OLLAMA_MODEL` en `.env`. **Probar el tool-calling antes**: no todos los 7B se comportan igual |
| Cambiar la pol�tica de rate limit | `middleware/security.py`, un valor por endpoint desde settings |
