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
    async def fake_run_agent(message, history=None, *, db=None):
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


async def test_chat_redacts_ids_in_unsafe_answer(auth_client, monkeypatch):
    async def fake_run_agent(message, history=None, *, db=None):
        return "El id es 507f1f77bcf86cd799439011", []

    monkeypatch.setattr(assistant.agent, "run_agent", fake_run_agent)

    resp = await auth_client.post(
        "/chat", json={"thread_id": "hilo-3", "message": "dame el id del producto"}
    )
    assert resp.status_code == 200
    assert resp.json()["response"] == "El id es un id interno"


async def test_chat_write_requires_ui_confirmation(auth_client, monkeypatch):
    async def fake_run_agent(message, history=None, *, db=None):
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

    import re

    confirmation = confirmed.json()["response"]
    assert confirmation.startswith("Crear cliente Lucía Confirmada. Hecho.")
    assert re.search(r"\b[0-9a-f]{24}\b", confirmation) is None

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


def _stub_write_tool(name="crear_venta", schema=None):
    from types import SimpleNamespace

    return SimpleNamespace(
        name=name,
        description="Registra una venta.",
        args_schema=schema
        or {
            "type": "object",
            "properties": {
                "cliente_id": {"type": "string"},
                "items": {"type": "array"},
                "notas": {"type": "string", "default": ""},
                "pago_porcentaje": {
                    "type": "number",
                    "default": 0,
                    "minimum": 0,
                    "maximum": 100,
                },
                "pago_tipo": {
                    "type": "string",
                    "enum": ["adelanto", "pago"],
                    "default": "adelanto",
                },
            },
            "required": ["cliente_id", "items"],
        },
    )


def test_signatures_text_shows_exact_arguments():
    from app.services.llm import agent

    text = agent.signatures_text([_stub_write_tool()])
    assert "crear_venta(" in text
    assert "cliente_id: (texto)!" in text
    assert "pago_tipo: (adelanto | pago)" in text
    assert "pago_porcentaje: (número) = 0" in text
    assert agent.signatures_text([]) == ""


def test_propose_tool_rejects_arguments_that_do_not_match_the_signature():
    from app.services.llm import agent

    propose = agent._propose_tool([_stub_write_tool()])

    valid = propose.invoke(
        {
            "herramienta": "crear_venta",
            "argumentos": {"cliente_id": "1", "items": [{"qty": 7}]},
            "resumen": "Venta",
        }
    )
    assert "registrada" in valid.lower()

    invalid = propose.invoke(
        {
            "herramienta": "crear_venta",
            "argumentos": {"cliente": {"nombre": "Marta"}, "estado": "pendiente"},
            "resumen": "Venta",
        }
    )
    assert "Argumentos inválidos para crear_venta" in invalid
    assert "falta 'cliente_id' (obligatorio)" in invalid
    assert "falta 'items' (obligatorio)" in invalid
    assert "'cliente' no es un parámetro de crear_venta" in invalid

    unknown_tool = propose.invoke({"herramienta": "borrar_todo", "argumentos": {}, "resumen": "x"})
    assert "no es una acción válida" in unknown_tool

    bad_enum = propose.invoke(
        {
            "herramienta": "crear_venta",
            "argumentos": {
                "cliente_id": "1",
                "items": [],
                "pago_tipo": "seña",
                "pago_porcentaje": 150,
            },
            "resumen": "x",
        }
    )
    assert "'pago_tipo' debe ser uno de: adelanto, pago" in bad_enum
    assert "'pago_porcentaje' debe ser menor o igual a 100" in bad_enum


def test_write_call_is_converted_to_a_proposal_and_never_executed():
    from app.services.llm import agent

    write_tools = [_stub_write_tool()]

    entry = agent._write_proposal(
        write_tools,
        {
            "name": "crear_venta",
            "args": {
                "cliente_id": "1",
                "items": [{"qty": 7}],
                "pago_porcentaje": 50,
                "notas": "Envío por Andreani",
            },
        },
    )
    assert entry["name"] == "proponer_accion"
    assert entry["arguments"]["herramienta"] == "crear_venta"
    assert entry["arguments"]["argumentos"]["cliente_id"] == "1"
    assert "seña del 50%" in entry["arguments"]["resumen"]
    assert "Andreani" in entry["arguments"]["resumen"]
    assert entry["ok"] is True
    assert "propuesta registrada" in entry["result"].lower()

    invalid = agent._write_proposal(write_tools, {"name": "crear_venta", "args": {"cliente": {}}})
    assert invalid["name"] == "crear_venta"
    assert invalid["ok"] is False
    assert invalid["result"].startswith("Argumentos inválidos para crear_venta")
    assert "falta 'cliente_id' (obligatorio)" in invalid["result"]

    assert agent._result_ok("proponer_accion", "Propuesta registrada.")
    assert not agent._result_ok("proponer_accion", "Argumentos inválidos para crear_venta.")
    assert agent._result_ok("buscar_productos", [])
    assert not agent._result_ok("buscar_productos", {"error": "boom"})


def test_write_call_written_as_text_becomes_a_proposal():
    from app.services.llm import agent

    write_tools = [_stub_write_tool()]
    text = (
        "Te propongo esto:\n```json\n"
        'crear_venta(cliente_id="507f1f77bcf86cd799439011", '
        'items=[{"product_id": "507f1f77bcf86cd799439012", "qty": 7}], '
        'notas="Envío por Andreani", pago_porcentaje=50)\n```'
    )
    entry = agent._text_call_entry(text, write_tools)
    assert entry is not None
    assert entry["name"] == "proponer_accion"
    assert entry["arguments"]["herramienta"] == "crear_venta"
    assert entry["arguments"]["argumentos"]["cliente_id"] == "507f1f77bcf86cd799439011"
    assert entry["ok"] is True
    assert "7 unidades" in entry["arguments"]["resumen"]

    reply = agent._proposal_reply(entry)
    assert reply.startswith("Propuesta registrada:")
    assert "507f1f77bcf86cd799439011" not in reply


def test_propose_call_written_as_text_becomes_a_proposal():
    from app.services.llm import agent

    write_tools = [_stub_write_tool()]
    text = (
        "```json\n"
        'proponer_accion(herramienta="crear_venta", '
        'argumentos={"cliente_id": "507f1f77bcf86cd799439011", "items": []}, '
        'resumen="Venta para Marta")\n```'
    )
    entry = agent._text_call_entry(text, write_tools)
    assert entry is not None
    assert entry["ok"] is True
    assert entry["arguments"]["resumen"] == "Venta para Marta"

    invalid = agent._text_call_entry("crear_venta(items=[])", write_tools)
    assert invalid is not None
    assert invalid["ok"] is False
    assert "falta 'cliente_id'" in invalid["result"]

    assert agent._text_call_entry("¿Cuánto stock hay en el depósito?", write_tools) is None


async def test_check_references_rejects_invented_ids(db):
    from app.services.llm import agent

    problems = await agent.check_references(
        db, "reponer_stock", {"producto_id": "persa_roja", "cantidad": 10}
    )
    assert problems
    assert "no existe el producto" in problems[0]

    problems = await agent.check_references(
        db,
        "crear_venta",
        {"cliente_id": "no-existe", "items": [{"description": "x", "qty": 2}]},
    )
    assert any("cliente" in problem for problem in problems)

    assert await agent.check_references(None, "crear_venta", {"cliente_id": "x"}) == []


async def test_reference_feedback_suggests_real_ids(db):
    from bson import ObjectId

    from app.repositories import products as products_repo
    from app.services.llm import agent

    provider = await products_repo.create_provider(db, {"name": "Proveedor IA", "active": True})
    product = await products_repo.create_product(
        db,
        {
            "name": "Alfombra persa roja",
            "category": "alfombras",
            "price": 45000,
            "cost": 20000,
            "stock": 7,
            "min_stock": 2,
            "unit": "unidad",
            "provider_id": ObjectId(str(provider.id)),
            "active": True,
        },
    )

    feedback = await agent.reference_feedback(
        db, "reponer_stock", {"producto_id": "alfombra-persa-roja", "cantidad": 10}
    )
    assert feedback is not None
    assert "no existe el producto" in feedback
    assert product.name in feedback
    assert str(product.id) in feedback

    ok = await agent.reference_feedback(
        db, "reponer_stock", {"producto_id": str(product.id), "cantidad": 10}
    )
    assert ok is None


def test_has_proposal_detects_registered_proposal_only():
    from app.services.llm import agent

    log = [
        {"name": "listar_clientes", "arguments": {}, "result": [], "ok": True},
        {"name": "crear_cliente", "arguments": {}, "result": "Argumentos inválidos", "ok": False},
    ]
    assert agent._has_proposal(log) is False
    log.append(
        {"name": "proponer_accion", "arguments": {}, "result": "Propuesta registrada", "ok": True}
    )
    assert agent._has_proposal(log) is True


def test_summary_for_hides_ids_and_uses_spanish():
    from app.services.llm import agent

    assert agent._summary_for("crear_cliente", {"nombre": "Marta"}) == "Crear cliente Marta"
    assert agent._summary_for("cancelar_venta", {}) == "Cancelar la venta"
    assert (
        agent._summary_for("registrar_pago", {"monto": 3750, "tipo": "adelanto"})
        == "Seña de 3750 pesos"
    )
    venta = agent._summary_for(
        "crear_venta",
        {
            "items": [{"qty": 7}],
            "pago_porcentaje": 50,
            "notas": "Envío por Andreani",
        },
    )
    assert venta == "Crear venta de 7 unidades con seña del 50% (Envío por Andreani)"
    assert (
        agent._summary_for("reponer_stock", {"cantidad": 10, "precio_venta": 35000})
        == "Reponer stock: sumar 10 unidades al stock y poner el precio de venta en 35000 pesos"
    )


def test_validate_args_reports_types():
    from app.services.llm import agent

    schema = {
        "type": "object",
        "properties": {"monto": {"type": "integer"}},
        "required": ["monto"],
    }
    assert agent.validate_args("registrar_pago", schema, {"monto": "mil"}) == [
        "'monto' debe ser número entero"
    ]
    assert agent.validate_args("registrar_pago", schema, {"monto": 500}) == []
    assert agent.validate_args("registrar_pago", {}, {"monto": 500}) == []


def test_pending_from_skips_rejected_proposal():
    from app.services.llm import assistant

    calls = [
        {
            "name": "proponer_accion",
            "arguments": {
                "herramienta": "crear_venta",
                "argumentos": {"cliente": {}},
                "resumen": "Mala",
            },
            "result": "Argumentos inválidos para crear_venta: falta 'cliente_id' (obligatorio).",
            "ok": True,
        },
        {
            "name": "proponer_accion",
            "arguments": {
                "herramienta": "crear_venta",
                "argumentos": {"cliente_id": "1", "items": [{"qty": 7}]},
                "resumen": "Venta de 7 soportes",
            },
            "result": "Propuesta registrada.",
            "ok": True,
        },
    ]
    pending = assistant._pending_from(calls, user_id="u-rechazo", thread_id="t-rechazo")
    assert pending is not None
    assert pending["summary"] == "Venta de 7 soportes"
    assert pending["args"] == {"cliente_id": "1", "items": [{"qty": 7}]}

    only_rejected = assistant._pending_from(calls[:1], user_id="u-2", thread_id="t-2")
    assert only_rejected is None


def test_summarize_validation_extracts_spanish_problems():
    from app.services.llm import assistant

    text = (
        "7 validation errors for call[crear_venta]\n"
        "cliente_id\n"
        "  Missing required argument [type=missing_argument, input_value={}, input_type=dict]\n"
        "  For further information visit https://errors.pydantic.dev/2.13/\n"
        "cliente\n"
        "  Unexpected keyword argument [type=unexpected_keyword_argument, input_value={}, "
        "input_type=dict]\n"
    )
    summary = assistant._summarize_validation(text)
    assert summary.startswith("crear_venta:")
    assert "falta 'cliente_id' (obligatorio)" in summary
    assert "'cliente' no es un parámetro de crear_venta" in summary

    failure = assistant._result_failure({"texto": text})
    assert failure is not None and "crear_venta" in failure
    assert assistant._result_failure({"texto": "todo bien"}) is None
    assert assistant._result_failure({"error": "La venta no existe"}) == "La venta no existe"


async def test_chat_confirm_rejects_invalid_arguments(auth_client, user):
    from app.services import pending_actions

    entry = pending_actions.create(
        user_id=str(user.id),
        thread_id="hilo-args-invalidos",
        tool="crear_venta",
        args={"cliente": {}, "estado": "pendiente"},
        summary="Venta inválida",
    )
    resp = await auth_client.post(
        "/chat/confirm", json={"thread_id": "hilo-args-invalidos", "token": entry["token"]}
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert "falta 'cliente_id' (obligatorio)" in detail
    assert "'cliente' no es un parámetro de crear_venta" in detail


def test_write_tools_never_reach_the_agent():
    from app.services.llm import agent

    propose = agent._propose_tool(
        [
            _stub_write_tool(
                name="crear_cliente",
                schema={
                    "type": "object",
                    "properties": {"nombre": {"type": "string"}},
                    "required": ["nombre"],
                },
            )
        ]
    )
    assert propose.name == "proponer_accion"
    assert agent.WRITE_TOOLS == {
        "crear_cliente",
        "crear_venta",
        "registrar_pago",
        "cancelar_venta",
        "reponer_stock",
    }
    result = propose.invoke(
        {
            "herramienta": "crear_cliente",
            "argumentos": {"nombre": "Nora"},
            "resumen": "Crear cliente",
        }
    )
    assert "registrada" in result.lower()

    read_only = propose.invoke({"herramienta": "listar_clientes", "argumentos": {}, "resumen": "x"})
    assert "no es una acción válida" in read_only


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
