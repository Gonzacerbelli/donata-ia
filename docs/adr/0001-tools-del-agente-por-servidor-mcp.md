# 0001. Tools del agente expuestas por un servidor MCP propio

**Estado:** Aceptada
**Fecha:** 20261006
**Contexto:** El asistente (CU07) necesita ejecutar operaciones de negocio (buscar productos,
crear ventas, registrar pagos). Hay que decidir **dónde** se declaran esas capacidades y cómo
las descubre el modelo.

## Alternativas consideradas

1. **Tools inline en el agente** — funciones decoradas con `@tool` dentro de `agent.py`.
   - A favor: menos piezas, un archivo.
   - En contra: mezcla el negocio con el agente; para probar una tool hay que instanciar el
     agente completo; difícil reutilizar las mismas capacidades desde otro cliente.
2. **Golpear la API HTTP interna desde el agente** — el agente llama a `http://localhost:8000`.
   - A favor: reutiliza exactamente los endpoints.
   - En contra: acopla el agente al transporte HTTP, agrega latencia y obliga a manejar auth
     del propio backend contra sí mismo.
3. **Servidor MCP propio (`donata-mcp`) + `langchain-mcp-adapters`** — elegida.
   - A favor: protocolo estándar; tools testeables de forma aislada por stdio; el agente queda
     desacoplado; cubre el requisito de MCP **dentro de la arquitectura**.
   - En contra: una pieza más (proceso hijo); hay que pasar el entorno explícito; debugging un
     poco más indirecto.

## Decisión

Se implementa `backend/app/mcp_server.py` con **FastMCP**, transporte **stdio**, exponiendo 12
herramientas en español. Cada tool **envuelve un `service`** (nunca un repositorio), por lo que
hereda todas las invariantes de negocio. El agente las consume con `MultiServerMCPClient`.

## Consecuencias

**A favor:** las tools se prueban sin LLM (hablando MCP por stdio); el negocio no se duplica;
MCP aparece en la arquitectura del producto, no sólo en el tooling de desarrollo.

**En contra:** el subproceso MCP no hereda el `.env` del compose → se inyecta el entorno de
forma explícita (`agent._server_env()`). Es el error que costó una iteración en el E2E.

**Impacto en el código:** `backend/app/mcp_server.py`, `backend/app/services/llm/agent.py`,
`backend/tests/test_mcp_server.py`.