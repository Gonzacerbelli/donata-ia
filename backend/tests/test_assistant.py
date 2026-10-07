from app.services.llm import assistant, guardrails


async def test_chat_blocks_off_topic(auth_client):
    resp = await auth_client.post(
        "/chat", json={"thread_id": "hilo-1", "message": "¿quién ganó el mundial de fútbol?"}
    )
    assert resp.status_code == 200
    assert resp.json()["response"] == guardrails.OUT_OF_SCOPE_REPLY
    assert resp.json()["tool_calls"] == []

    messages = await auth_client.get("/chat/threads/hilo-1/messages")
    roles = [m["role"] for m in messages.json()]
    assert roles == ["user", "assistant"]


async def test_chat_uses_agent_and_persists_tool_calls(auth_client, monkeypatch):
    async def fake_run_agent(message, history=None):
        return "Tenés 3 productos con stock.", [
            {"name": "buscar_productos", "arguments": {"query": ""}, "result": [], "ok": True}
        ]

    monkeypatch.setattr(assistant.agent, "run_agent", fake_run_agent)

    resp = await auth_client.post(
        "/chat", json={"thread_id": "hilo-2", "message": "¿cuántos productos tengo con stock?"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["response"] == "Tenés 3 productos con stock."
    assert body["tool_calls"][0]["name"] == "buscar_productos"

    messages = await auth_client.get("/chat/threads/hilo-2/messages")
    assistant_msg = messages.json()[-1]
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["tool_calls"][0]["name"] == "buscar_productos"


async def test_chat_guards_unsafe_answer(auth_client, monkeypatch):
    async def fake_run_agent(message, history=None):
        return "El id es 507f1f77bcf86cd799439011", []

    monkeypatch.setattr(assistant.agent, "run_agent", fake_run_agent)

    resp = await auth_client.post(
        "/chat", json={"thread_id": "hilo-3", "message": "dame el id del producto"}
    )
    assert resp.status_code == 200
    assert resp.json()["response"] == guardrails.GUARDED_REPLY
