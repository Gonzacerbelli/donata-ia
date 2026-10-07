import json
from typing import Any

from ...config import settings
from ...core.errors import DependencyUnavailableError, NotFoundError, UnprocessableError
from .. import chat_history, pending_actions
from . import agent, guardrails

WRITE_TOOLS = agent.WRITE_TOOLS


def _normalize_args(raw: Any) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _pending_from(tool_calls: list[dict], *, user_id: str, thread_id: str) -> dict | None:
    for entry in tool_calls:
        if entry.get("name") != "proponer_accion":
            continue
        arguments = entry.get("arguments") or {}
        tool = str(arguments.get("herramienta") or "")
        if tool not in WRITE_TOOLS:
            return None
        return pending_actions.create(
            user_id=user_id,
            thread_id=thread_id,
            tool=tool,
            args=_normalize_args(arguments.get("argumentos", arguments.get("argumentos_json"))),
            summary=str(arguments.get("resumen") or tool),
        )
    return None


async def handle_message(db, user_id: str, thread_id: str, message: str) -> dict:
    await chat_history.create_thread(db, user_id, thread_id)
    await chat_history.append_message(db, thread_id, "user", message)

    if settings.guardrails_enabled and guardrails.is_off_topic(message):
        reply = guardrails.OUT_OF_SCOPE_REPLY
        await chat_history.append_message(db, thread_id, "assistant", reply)
        return {
            "thread_id": thread_id,
            "response": reply,
            "tool_calls": [],
            "pending_action": None,
        }

    history = await chat_history.list_messages(
        db, user_id, thread_id, limit=settings.chat_history_limit
    )
    prior = [(m.role, m.content) for m in history[:-1]]

    try:
        reply, tool_calls = await agent.run_agent(message, prior)
    except Exception as exc:
        raise DependencyUnavailableError("El asistente no está disponible en este momento") from exc

    pending = None
    if settings.guardrails_enabled:
        issues = guardrails.validate_answer(reply)
        if issues:
            reply = guardrails.GUARDED_REPLY
            tool_calls = []
        else:
            pending = _pending_from(tool_calls, user_id=user_id, thread_id=thread_id)
    else:
        pending = _pending_from(tool_calls, user_id=user_id, thread_id=thread_id)

    await chat_history.append_message(db, thread_id, "assistant", reply, tool_calls=tool_calls)
    return {
        "thread_id": thread_id,
        "response": reply,
        "tool_calls": tool_calls,
        "pending_action": pending,
    }


def _unwrap_result(result: Any) -> Any:
    if isinstance(result, list) and result and isinstance(result[0], dict) and "text" in result[0]:
        try:
            return json.loads(result[0]["text"])
        except (TypeError, ValueError):
            return {"texto": str(result[0]["text"])}
    return result


async def confirm_pending(db, user_id: str, thread_id: str, token: str) -> dict:
    entry = pending_actions.pop(user_id=user_id, thread_id=thread_id, token=token)
    if entry is None:
        raise NotFoundError("La acción propuesta ya no está vigente")

    if entry["tool"] not in WRITE_TOOLS:
        raise UnprocessableError("Esa acción no está permitida")

    tools = await agent.load_tools()
    tool = next((t for t in tools if t.name == entry["tool"]), None)
    if tool is None:
        raise NotFoundError("La herramienta solicitada no existe")

    try:
        result = _unwrap_result(await tool.ainvoke(entry["args"]))
    except Exception as exc:
        raise UnprocessableError(f"No se pudo ejecutar: {exc}") from exc

    if isinstance(result, dict) and result.get("error"):
        raise UnprocessableError(f"No se pudo ejecutar: {result['error']}")

    summary = entry["summary"]
    payload = json.dumps(result, ensure_ascii=False, default=str)
    reply = f"{summary} Hecho. Resultado: {payload}"
    tool_call = {"name": entry["tool"], "arguments": entry["args"], "result": result, "ok": True}

    await chat_history.append_message(db, thread_id, "assistant", reply, tool_calls=[tool_call])
    return {
        "thread_id": thread_id,
        "response": reply,
        "tool_calls": [tool_call],
        "pending_action": None,
    }
