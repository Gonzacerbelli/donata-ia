import argparse
import asyncio

from app.db import close_db, connect_db, get_db
from app.repositories import products as products_repo
from app.services.llm import vector_store


async def _sync_products() -> int:
    await connect_db()
    try:
        db = await get_db()
        products = await products_repo.list_products(db, active_only=True)
        return vector_store.sync_products(products)
    finally:
        await close_db()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingesta de la base de conocimiento de Donata")
    parser.add_argument("--force", action="store_true", help="Reconstruye la colección desde cero")
    parser.add_argument("--products", action="store_true", help="Sincroniza también el catálogo")
    args = parser.parse_args()

    chunks = vector_store.ingest_knowledge_base(force=args.force)
    print(f"Base de conocimiento: {chunks} fragmentos indexados")

    if args.products:
        count = await _sync_products()
        print(f"Catálogo: {count} productos indexados")


if __name__ == "__main__":
    asyncio.run(main())
