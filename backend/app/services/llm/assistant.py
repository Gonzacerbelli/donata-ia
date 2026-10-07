from ...config import settings
from ...core.errors import DependencyUnavailableError
from .. import chat_history
from . import agent, guardrails


async def handle_message(db, user_id: str, thread_id: str, message: str) -> dict:
    await chat_history.create_thread(db, user_id, thread_id)
    await chat_history.append_message(db, thread_id, "user", message)

    if settings.guardrails_enabled and guardrails.is_off_topic(message):
        reply = guardrails.OUT_OF_SCOPE_REPLY
        await chat_history.append_message(db, thread_id, "assistant", reply)
        return {"thread_id": thread_id, "response": reply, "tool_calls": []}

    history = await chat_history.list_messages(
        db, user_id, thread_id, limit=settings.chat_history_limit
    )
    prior = [(m.role, m.content) for m in history[:-1]]

    try:
        reply, tool_calls = await agent.run_agent(message, prior)
    except Exception as exc:
        raise DependencyUnavailableError("El asistente no está disponible en este momento") from exc

    if settings.guardrails_enabled:
        issues = guardrails.validate_answer(reply)
        if issues:
            reply = guardrails.GUARDED_REPLY
            tool_calls = []

    await chat_history.append_message(db, thread_id, "assistant", reply, tool_calls=tool_calls)
    return {"thread_id": thread_id, "response": reply, "tool_calls": tool_calls}
