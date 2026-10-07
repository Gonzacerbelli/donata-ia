import os
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
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
- Si una consulta está fuera del negocio, aclaralo amablemente.
"""

MAX_STEPS = 6


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
    tools = await load_tools()
    tool_map = {tool.name: tool for tool in tools}
    llm = get_llm(temperature=0).bind_tools(tools)

    messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
    messages.extend(_to_lc_messages(history or []))
    messages.append(HumanMessage(content=message))

    tool_calls_log: list[dict[str, Any]] = []
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
