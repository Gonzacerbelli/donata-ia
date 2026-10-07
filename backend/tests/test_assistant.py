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


async def test_chat_write_requires_ui_confirmation(auth_client, monkeypatch):
    async def fake_run_agent(message, history=None):
        return (
            "Puedo crear el cliente. ¿Confirmás?",
            [
                {
                    "name": "proponer_accion",
                    "arguments": {
                        "herramienta": "crear_cliente",
                        "argumentos": {"nombre": "Lucía Confirmada"},
                        "resumen": "Crear cliente Lucía Confirmada",
                    },
                    "result": "Propuesta registrada",
                    "ok": True,
                }
            ],
        )

    monkeypatch.setattr(assistant.agent, "run_agent", fake_run_agent)

    resp = await auth_client.post(
        "/chat", json={"thread_id": "hilo-4", "message": "creá un cliente"}
    )
    assert resp.status_code == 200
    pending = resp.json()["pending_action"]
    assert pending["tool"] == "crear_cliente"
    assert pending["summary"] == "Crear cliente Lucía Confirmada"

    clients = await auth_client.get("/clients?search=Lucía Confirmada")
    assert clients.json() == []

    confirmed = await auth_client.post(
        "/chat/confirm", json={"thread_id": "hilo-4", "token": pending["token"]}
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["pending_action"] is None

    clients = await auth_client.get("/clients?search=Lucía Confirmada")
    assert [c["name"] for c in clients.json()] == ["Lucía Confirmada"]


async def test_chat_confirm_rejects_unknown_token(auth_client):
    resp = await auth_client.post(
        "/chat/confirm", json={"thread_id": "hilo-5", "token": "no-existe"}
    )
    assert resp.status_code == 404


def test_unwrap_result_decodes_mcp_content_blocks():
    from app.services.llm import assistant

    raw = [{"type": "text", "text": '{"nombre": "Nora"}'}]
    assert assistant._unwrap_result(raw) == {"nombre": "Nora"}
    assert assistant._unwrap_result({"id": "1"}) == {"id": "1"}


def test_pending_action_accepts_dict_or_json_string():
    from app.services.llm import assistant

    calls = [
        {
            "name": "proponer_accion",
            "arguments": {
                "herramienta": "crear_cliente",
                "argumentos": '{"nombre": "Ana Lunes"}',
                "resumen": "Crear cliente Ana Lunes",
            },
        }
    ]
    pending = assistant._pending_from(calls, user_id="u-normalize", thread_id="t-normalize")
    assert pending is not None
    assert pending["args"] == {"nombre": "Ana Lunes"}

    calls[0]["arguments"]["argumentos"] = {"nombre": "Ana Martes"}
    pending = assistant._pending_from(calls, user_id="u-normalize-2", thread_id="t-normalize-2")
    assert pending is not None
    assert pending["args"] == {"nombre": "Ana Martes"}


def test_write_tools_never_reach_the_agent():
    from app.services.llm import agent

    propose = agent._propose_tool()
    assert propose.name == "proponer_accion"
    assert agent.WRITE_TOOLS == {
        "crear_cliente",
        "crear_venta",
        "registrar_pago",
        "cancelar_venta",
    }
    result = propose.invoke(
        {
            "herramienta": "crear_cliente",
            "argumentos": {"nombre": "Nora"},
            "resumen": "Crear cliente",
        }
    )
    assert "registrada" in result.lower()
