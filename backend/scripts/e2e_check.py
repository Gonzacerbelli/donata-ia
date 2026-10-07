"""Chequeo end-to-end del asistente con Ollama real.

Uso:
    docker compose run --rm --no-deps api python -m scripts.e2e_check
"""

import asyncio

from bson import ObjectId

from app.db import close_db, connect_db, get_db
from app.repositories import clients as clients_repo
from app.repositories import products as products_repo
from app.services.llm import agent, rag


async def _seed(db) -> None:
    provider = await products_repo.create_provider(db, {"name": "Proveedor E2E", "active": True})
    await products_repo.create_product(
        db,
        {
            "name": "Alfombra persa roja",
            "category": "alfombras",
            "description": "Alfombra artesanal de lana, 2x3 metros",
            "price": 45000,
            "price_mayorista": 38000,
            "cost": 20000,
            "stock": 7,
            "min_stock": 2,
            "provider_id": ObjectId(str(provider.id)),
            "active": True,
        },
    )
    await clients_repo.create_client(db, {"name": "Cliente E2E", "type": "mayorista"})


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

    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
