"""Chequeo end-to-end del asistente con Ollama real.

Uso:
    docker compose run --rm --no-deps api python -m scripts.e2e_check
"""

import asyncio
import time

from bson import ObjectId

from app.db import close_db, connect_db, get_db
from app.repositories import clients as clients_repo
from app.repositories import products as products_repo
from app.services import chat_history
from app.services.llm import agent, assistant, guardrails, rag

ORDEN_DE_EJEMPLO = (
    "quiero crear una orden para marta de avenida libertador 312, cordoba. "
    "compro 7 soporte para plantas trípode, pago la mitad con seña y se envia por andreani. "
    "el numero de telefono es 1165245400"
)


async def _seed(db) -> None:
    providers = await products_repo.list_providers(db, active_only=True)
    provider = next((p for p in providers if p.name == "Proveedor E2E"), None)
    if provider is None:
        provider = await products_repo.create_provider(
            db, {"name": "Proveedor E2E", "active": True}
        )

    productos = [
        {
            "name": "Alfombra persa roja",
            "category": "alfombras",
            "description": "Alfombra artesanal de lana, 2x3 metros",
            "price": 45000,
            "price_mayorista": 38000,
            "cost": 20000,
            "stock": 7,
            "min_stock": 2,
        },
        {
            "name": "Soporte para plantas trípode",
            "category": "accesorios",
            "price": 2500,
            "cost": 1200,
            "stock": 12,
            "min_stock": 2,
        },
    ]
    existentes = await products_repo.list_products(db, active_only=True)
    for producto in productos:
        if any(p.name == producto["name"] for p in existentes):
            continue
        await products_repo.create_product(
            db,
            {
                **producto,
                "unit": "unidad",
                "provider_id": ObjectId(str(provider.id)),
                "active": True,
            },
        )

    clientes = await clients_repo.list_clients(db)
    if not any(c.name == "Cliente E2E" for c in clientes):
        await clients_repo.create_client(db, {"name": "Cliente E2E", "type": "mayorista"})


async def _assert_refs_exist(db, args: dict) -> None:
    problems = await agent.check_references(db, "", args)
    assert not problems, f"la propuesta usa ids inventados: {problems}"


async def main() -> None:
    await connect_db()
    db = await get_db()
    await _seed(db)

    print("\n=== 1) Consulta de datos (debe usar herramientas MCP) ===")
    reply, calls = await agent.run_agent(
        "¿Cuántos productos tengo en el catálogo y cuánto stock hay?", []
    )
    print("Respuesta:", reply)
    print("Herramientas usadas:", [c["name"] for c in calls])

    print("\n=== 2) Consulta de documentación (RAG) ===")
    print(await rag.answer_question_async("¿Cómo se calculan los precios mayoristas?"))

    print("\n=== 3) Propuesta de escritura con Ollama real ===")
    assert not guardrails.is_off_topic(ORDEN_DE_EJEMPLO), "el pedido quedó fuera de tema"
    thread_id = f"hilo-e2e-{int(time.time() * 1000)}"
    result = await assistant.handle_message(db, "e2e-check", thread_id, ORDEN_DE_EJEMPLO)
    print("Respuesta:", result["response"])
    print("Tool calls:", [c["name"] for c in result["tool_calls"]])
    pending = result["pending_action"]
    assert pending is not None, "el asistente no propuso ninguna acción"
    print("Acción propuesta:", pending["tool"], "-", pending["summary"])
    print("Argumentos:", pending["args"])

    tools = await agent.load_tools()
    tool = next(t for t in tools if t.name == pending["tool"])
    problems = agent.validate_args(pending["tool"], agent.tool_schema(tool), pending["args"])
    assert not problems, f"argumentos inválidos: {problems}"
    if pending["tool"] == "crear_cliente":
        assert pending["args"]["nombre"].lower().startswith("marta"), pending["args"]
        assert pending["args"].get("direccion"), "falta la dirección de entrega"
        assert pending["args"].get("telefono"), "falta el teléfono"
    elif pending["tool"] == "crear_venta":
        assert pending["args"]["items"][0]["qty"] == 7, pending["args"]
        assert pending["args"].get("pago_porcentaje") == 50, pending["args"]
        assert pending["args"].get("notas"), "falta el detalle de envío en notas"
        await _assert_refs_exist(db, pending["args"])
    else:
        raise AssertionError(f"acción inesperada: {pending['tool']}")
    print("Argumentos válidos contra la firma real de la herramienta ✓")

    print("\n=== 4) Reposición de stock con precio ===")
    reposicion = (
        "quiero reponer stock de alfombra persa roja, 10 unidades, con precio de venta de 35000"
    )
    assert not guardrails.is_off_topic(reposicion), "la reposición quedó fuera de tema"
    assert guardrails.mentions_write_action(reposicion), "no detectó la acción de escritura"
    thread_2 = f"hilo-e2e-reposicion-{int(time.time() * 1000)}"
    result = await assistant.handle_message(db, "e2e-check", thread_2, reposicion)
    print("Respuesta:", result["response"])
    print("Tool calls:", [c["name"] for c in result["tool_calls"]])
    pending = result["pending_action"]
    assert pending is not None, "el asistente no propuso la reposición"
    assert pending["tool"] == "reponer_stock", pending["tool"]
    assert pending["args"]["cantidad"] == 10, pending["args"]
    assert pending["args"]["precio_venta"] == 35000, pending["args"]
    await _assert_refs_exist(db, pending["args"])
    product = await products_repo.get_product(db, pending["args"]["producto_id"])
    assert product is not None and product.name == "Alfombra persa roja", pending["args"]
    print("Acción propuesta:", pending["tool"], "-", pending["summary"])
    print("Argumentos:", pending["args"])

    print("\n=== 5) Streaming SSE con Ollama real ===")
    assert not guardrails.is_off_topic(ORDEN_DE_EJEMPLO), "el pedido quedó fuera de tema"
    thread_3 = f"hilo-e2e-stream-{int(time.time() * 1000)}"
    await chat_history.create_thread(db, "e2e-check", thread_3)
    events = []
    async for event, payload in assistant.stream_message(
        db, "e2e-check", thread_3, ORDEN_DE_EJEMPLO
    ):
        events.append((event, payload))
        if event == "token":
            print(payload["delta"], end="", flush=True)
    print()

    names = [name for name, _ in events]
    assert names[0] == "start", f"el primer evento debe ser start: {names}"
    assert names[-1] == "done", f"el último evento debe ser done: {names}"
    tokens = [p["delta"] for n, p in events if n == "token"]
    assert tokens, "no se recibió ningún token incremental"
    text = "".join(tokens)
    assert text.strip(), "el texto acumulado del stream quedó vacío"
    final = events[-1][1]
    assert final["response"].strip(), "done sin respuesta"
    assert final["pending_action"] is not None, "done sin pending_action"
    assert final["pending_action"]["tool"] in {"crear_cliente", "crear_venta"}
    pendings = [n for n, _ in events if n == "pending_action"]
    assert pendings == ["pending_action"], f"pending_action duplicado: {names}"
    assert names.index("pending_action") == len(names) - 2, (
        "pending_action debe ir justo antes de done"
    )
    print(f"Eventos: {names}")
    print(f"Tokens incrementales: {len(tokens)}")
    print(f"Acción propuesta: {final['pending_action']['tool']}")
    print("Streaming verificado contra Ollama real ✓")

    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
