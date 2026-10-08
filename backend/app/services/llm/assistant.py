import asyncio
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


def _proposal_accepted(entry: dict) -> bool:
    result = entry.get("result")
    if not isinstance(result, str):
        return True
    return "propuesta registrada" in result.lower()


def _pending_from(tool_calls: list[dict], *, user_id: str, thread_id: str) -> dict | None:
    for entry in tool_calls:
        if entry.get("name") != "proponer_accion":
            continue
        if not _proposal_accepted(entry):
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


async def _finalize_turn(
    db, user_id: str, thread_id: str, reply: str, tool_calls: list[dict]
) -> dict:
    pending = None
    if settings.guardrails_enabled:
        reply = guardrails.sanitize_answer(reply)
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
        reply, tool_calls = await agent.run_agent(message, prior, db=db)
    except Exception as exc:
        raise DependencyUnavailableError("El asistente no está disponible en este momento") from exc

    return await _finalize_turn(db, user_id, thread_id, reply, tool_calls)


async def stream_message(db, user_id: str, thread_id: str, message: str):
    """Genera los eventos (evento, payload) de un turno para transmitir por SSE."""
    yield "start", {"thread_id": thread_id}

    if settings.guardrails_enabled and guardrails.is_off_topic(message):
        reply = guardrails.OUT_OF_SCOPE_REPLY
        await chat_history.append_message(db, thread_id, "user", message)
        await chat_history.append_message(db, thread_id, "assistant", reply)
        yield (
            "done",
            {
                "thread_id": thread_id,
                "response": reply,
                "tool_calls": [],
                "pending_action": None,
            },
        )
        return

    history = await chat_history.list_messages(
        db, user_id, thread_id, limit=settings.chat_history_limit
    )
    prior = [(m.role, m.content) for m in history]

    queue: asyncio.Queue = asyncio.Queue()
    outcome: dict[str, Any] = {}

    async def emit(event: str, payload: dict) -> None:
        await queue.put((event, payload))

    async def run() -> None:
        try:
            reply, tool_calls = await agent.run_agent(message, prior, db=db, emit=emit)
            outcome["reply"] = reply
            outcome["tool_calls"] = tool_calls
        except Exception:
            outcome["error"] = "El asistente no está disponible en este momento"
        finally:
            await queue.put((None, None))

    task = asyncio.create_task(run())
    try:
        while True:
            event, payload = await queue.get()
            if event is None:
                break
            yield event, payload
    finally:
        task.cancel()

    if "error" in outcome:
        await chat_history.append_message(db, thread_id, "user", message)
        yield "error", {"detail": outcome["error"]}
        return

    await chat_history.append_message(db, thread_id, "user", message)
    result = await _finalize_turn(db, user_id, thread_id, outcome["reply"], outcome["tool_calls"])
    if result["pending_action"] is not None:
        yield "pending_action", result["pending_action"]
    yield "done", result


def _unwrap_result(result: Any) -> Any:
    if isinstance(result, list) and result and isinstance(result[0], dict) and "text" in result[0]:
        try:
            return json.loads(result[0]["text"])
        except (TypeError, ValueError):
            return {"texto": str(result[0]["text"])}
    return result


def _summarize_validation(text: str) -> str:
    first_line = text.splitlines()[0] if text.splitlines() else text
    tool_name = (
        first_line.split("call[")[-1].rstrip("]") if "call[" in first_line else "la operación"
    )
    lines = [
        line.strip()
        for line in text.splitlines()[1:]
        if line.strip() and not line.strip().startswith("For further information")
    ]
    problems: list[str] = []
    for index in range(0, len(lines) - 1, 2):
        field, detail = lines[index], lines[index + 1]
        if detail.startswith("Missing required"):
            problems.append(f"falta '{field}' (obligatorio)")
        elif detail.startswith("Unexpected keyword"):
            problems.append(f"'{field}' no es un parámetro de {tool_name}")
        else:
            problems.append(f"{field}: {detail.split(' [type=')[0]}")
    if not problems:
        return first_line
    return f"{tool_name}: {'; '.join(problems)}"


def _describe_failure(exc: Exception) -> str:
    text = str(exc)
    if "validation error" in text:
        return _summarize_validation(text)
    return text


def _result_failure(result: Any) -> str | None:
    if not isinstance(result, dict):
        return None
    if result.get("error"):
        return str(result["error"])
    text = result.get("texto")
    if isinstance(text, str) and (
        "validation error" in text or "Traceback (most recent call last)" in text
    ):
        return _summarize_validation(text)
    return None


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

    problems = agent.validate_args(entry["tool"], agent.tool_schema(tool), entry["args"])
    if problems:
        raise UnprocessableError("No se pudo ejecutar: " + "; ".join(problems))

    ref_problems = await agent.check_references(db, entry["tool"], entry["args"])
    if ref_problems:
        raise UnprocessableError("No se pudo ejecutar: " + "; ".join(ref_problems))

    try:
        result = _unwrap_result(await tool.ainvoke(entry["args"]))
    except Exception as exc:
        raise UnprocessableError(f"No se pudo ejecutar: {_describe_failure(exc)}") from exc

    failure = _result_failure(result)
    if failure:
        raise UnprocessableError(f"No se pudo ejecutar: {failure}")

    summary = str(entry["summary"]).rstrip(".")
    reply = guardrails.sanitize_answer(f"{summary}. Hecho. Revisá el resultado en la pantalla.")
    tool_call = {"name": entry["tool"], "arguments": entry["args"], "result": result, "ok": True}

    await chat_history.append_message(db, thread_id, "assistant", reply, tool_calls=[tool_call])
    return {
        "thread_id": thread_id,
        "response": reply,
        "tool_calls": [tool_call],
        "pending_action": None,
    }
