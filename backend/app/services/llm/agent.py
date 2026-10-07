import os
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool, tool
from langchain_mcp_adapters.client import MultiServerMCPClient

from ...config import settings
from .rag import get_llm

SYSTEM_PROMPT = """Sos el asistente operativo de Donata, un negocio de alfombras y textiles.
Ayudás a gestionar productos, stock, precios, clientes, proveedores, ventas, pagos y reportes.

Reglas:
- Respondé siempre en español, breve y claro.
- Para datos concretos (stock, precios, ventas, clientes) usá las herramientas
  disponibles; nunca inventes datos.
- Para dudas sobre el funcionamiento del negocio, usá la herramienta de documentación.
- Trabajás con pesos argentinos enteros; no uses decimales.
- Las herramientas de escritura no están disponibles: sólo podés consultar.
- Para crear, modificar, cancelar o registrar algo, usá `proponer_accion` con
  `herramienta` = nombre de la operación, `argumentos` = objeto JSON con los
  argumentos de esa operación (por ejemplo {"nombre": "Nora", "telefono": "1199998888"})
  y `resumen` = qué se va a hacer en una frase.
  Nada se ejecuta hasta que el usuario lo confirme en la pantalla.
- Cuando propongas una acción, terminá pidiendo la confirmación explícita del usuario.
- Si una consulta está fuera del negocio, aclaralo amablemente.
"""

MAX_STEPS = 6

WRITE_TOOLS = {"crear_cliente", "crear_venta", "registrar_pago", "cancelar_venta"}


def _server_env() -> dict[str, str]:
    return {
        **os.environ,
        "MONGO_URI": settings.mongo_uri,
        "MONGO_DB": settings.mongo_db,
        "CHROMA_DIR": settings.chroma_dir,
        "EMBEDDING_MODEL": settings.embedding_model,
        "OLLAMA_BASE_URL": settings.ollama_base_url,
        "OLLAMA_MODEL": settings.ollama_model,
        "RAG_TOP_K": str(settings.rag_top_k),
    }


def build_mcp_client() -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            "donata": {
                "command": "python",
                "args": ["-m", "app.mcp_server"],
                "transport": "stdio",
                "env": _server_env(),
            }
        }
    )


async def load_tools() -> list[BaseTool]:
    client = build_mcp_client()
    return await client.get_tools()


def _propose_tool() -> BaseTool:
    @tool
    def proponer_accion(herramienta: str, argumentos: dict | str, resumen: str) -> str:
        """Propone una acción de escritura que el usuario debe confirmar en la pantalla.

        No ejecuta nada. `herramienta` es el nombre de la operación (crear_cliente,
        crear_venta, registrar_pago, cancelar_venta), `argumentos` es el objeto JSON
        con los argumentos de esa operación y `resumen` describe la acción.
        """
        return (
            "Propuesta registrada. Respondé al usuario resumiendo la acción y pidiéndole "
            "que confirme en la pantalla; todavía no se ejecutó nada."
        )

    return proponer_accion


async def _read_tools() -> list[BaseTool]:
    tools = [tool for tool in await load_tools() if tool.name not in WRITE_TOOLS]
    return [*tools, _propose_tool()]


def _to_lc_messages(history: list[tuple[str, str]]) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for role, content in history:
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    return messages


async def run_agent(
    message: str, history: list[tuple[str, str]] | None = None
) -> tuple[str, list[dict[str, Any]]]:
    tool_calls_log: list[dict[str, Any]] = []
    tools = await _read_tools()
    tool_map = {tool.name: tool for tool in tools}
    llm = get_llm(temperature=0).bind_tools(tools)

    messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
    messages.extend(_to_lc_messages(history or []))
    messages.append(HumanMessage(content=message))

    for _ in range(MAX_STEPS):
        ai_message = await llm.ainvoke(messages)
        messages.append(ai_message)
        calls = getattr(ai_message, "tool_calls", None) or []
        if not calls:
            content = ai_message.content
            text = content if isinstance(content, str) else str(content)
            return text, tool_calls_log
        for call in calls:
            tool = tool_map.get(call["name"])
            result = await _invoke_tool(tool, call["args"])
            tool_calls_log.append(
                {
                    "name": call["name"],
                    "arguments": call["args"],
                    "result": result,
                    "ok": not (isinstance(result, dict) and result.get("error")),
                }
            )
            messages.append(ToolMessage(content=_stringify(result), tool_call_id=call["id"]))
    return (
        "No pude completar la consulta en varios intentos. ¿Podés reformularla?",
        tool_calls_log,
    )


async def _invoke_tool(tool: BaseTool | None, arguments: dict) -> Any:
    if tool is None:
        return {"error": "Herramienta desconocida"}
    try:
        return await tool.ainvoke(arguments)
    except Exception as exc:  # pragma: no cover - depende del servidor MCP
        return {"error": str(exc)}


def _stringify(value: Any) -> str:
    import json

    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(value)
