"""Datos de demostración realistas para Donata IA.

Genera proveedores, productos (macramé), clientes y órdenes distribuidas en el
último año, con pagos y estados variados, para que el dashboard y los listados
muestren información significativa.

Resetea las colecciones de negocio y de chat antes de sembrar, de modo que cada
corrida deja una base consistente (los usuarios se conservan). Cada cliente
queda con al menos una orden.

Uso:
    docker compose run --rm --no-deps api python -m scripts.seed_demo
"""

import asyncio
import random
from datetime import timedelta

from bson import ObjectId

from app.db import close_db, connect_db, get_db
from app.models import utcnow
from app.repositories import clients as clients_repo
from app.repositories import products as products_repo
from app.schemas.entities import PaymentCreate, SaleCreate, SaleItemIn, SaleUpdate
from app.services import sales as sales_service

RESET_COLLECTIONS = [
    "providers",
    "products",
    "clients",
    "sales",
    "stock_moves",
    "notification_states",
    "chat_messages",
    "chat_threads",
]

PROVIDERS = [
    {
        "name": "Hilos del Norte",
        "contact": "Marina López",
        "phone": "341-5551234",
        "email": "ventas@hilosdelnorte.com",
    },
    {
        "name": "Maderas del Litoral",
        "contact": "Jorge Pereyra",
        "phone": "342-4556789",
        "email": "contacto@maderaslitoral.com",
    },
    {
        "name": "Cuentas & Telas",
        "contact": "Sofía Ríos",
        "phone": "11-6789-1234",
        "email": "hola@cuentasytextil.com",
    },
    {"name": "Decor Natural", "contact": "Marcos Paz", "email": "ventas@donatanatural.com"},
]

PRODUCTS = [
    ("Maceta colgante Amanda", "macetas", 8500, 6800, 4200, 24, 6),
    ("Maceta colgante Nube", "macetas", 6200, 5000, 3000, 31, 8),
    ("Funda de macramé para olla", "cocina", 7200, 5800, 3500, 18, 5),
    ("Tapiz mural Luna", "decoracion", 24500, 19500, 12000, 9, 3),
    ("Tapiz mural Sol", "decoracion", 26000, 21000, 13500, 7, 3),
    ("Cortina de macramé", "decoracion", 32000, 27000, 17000, 6, 2),
    ("Espejo enmarcado en macramé", "decoracion", 28500, 23000, 15000, 8, 3),
    ("Corazón decorativo", "decoracion", 4500, 3600, 2100, 40, 10),
    ("Posavasos x4", "cocina", 3900, 3100, 1700, 52, 12),
    ("Aros de servilletas x6", "cocina", 5800, 4600, 2600, 27, 8),
    ("Bolsos de playa", "accesorios", 18500, 15000, 9500, 11, 4),
    ("Riñonera tejida", "accesorios", 16200, 13200, 8200, 14, 5),
    ("Guirnalda de macramé", "decoracion", 6900, 5500, 3300, 22, 7),
    ("Lámpara de macramé", "iluminacion", 21500, 17500, 11500, 10, 3),
    ("Soporte para plantas trípode", "macetas", 11000, 8900, 6000, 16, 5),
]

# name, type, phone, email, instagram, address, notes
CLIENTS = [
    (
        "Boutique Sol y Luna",
        "mayorista",
        "11-4001-2233",
        "hola@soyluna.com",
        "@boutiquesolyluna",
        "Av. Santa Fe 2450, CABA",
        "Compra por temporada, paga a 30 días",
    ),
    (
        "Deco Casa Norte",
        "mayorista",
        "11-4002-3344",
        "compras@decocasanorte.com",
        "@decocasanorte",
        "Av. Maipú 1180, Vicente López",
        None,
    ),
    (
        "Ana Pérez",
        "minorista",
        "11-5555-1010",
        "ana.perez@mail.com",
        "@anap",
        "Juncal 890, CABA",
        None,
    ),
    ("Martina Gómez", "minorista", "11-5555-2020", None, None, "Cabildo 1720, CABA", None),
    ("Lucas Fernández", "minorista", "11-5555-3030", "lucasf@mail.com", None, None, None),
    (
        "Sofía Rossi",
        "minorista",
        "11-5555-4040",
        None,
        "@sofiarossi",
        "Mitre 450, San Isidro",
        None,
    ),
    (
        "Regalería Capricho",
        "ambos",
        "11-4003-4455",
        "ventas@regaleriacapricho.com",
        "@regaleriacapricho",
        "Belgrano 210, Martínez",
        "Pide factura A",
    ),
    (
        "Camila Duarte",
        "minorista",
        "11-5555-5050",
        "camila.duarte@mail.com",
        "@cami",
        "Rivadavia 3300, CABA",
        None,
    ),
    ("Julián Vega", "minorista", "11-5555-6060", None, None, "Las Heras 2210, CABA", None),
    (
        "Casa & Estilo",
        "mayorista",
        "11-4004-5566",
        "compras@casaestilo.com",
        "@casaestilo",
        "Av. del Libertador 5600, CABA",
        None,
    ),
    (
        "Marta Ríos",
        "minorista",
        "11-5555-7070",
        "marta.rios@mail.com",
        None,
        "Av. Libertador 312, Córdoba",
        None,
    ),
    (
        "Almacén de Ramos",
        "ambos",
        "11-4005-6677",
        None,
        "@almacenderamos",
        "Alsina 55, Quilmes",
        None,
    ),
]

PAYMENT_METHODS = ["efectivo", "transferencia", "mercadopago", "tarjeta"]
STATUSES = ["pendiente", "en_proceso", "entregado", "entregado", "entregado", "cancelado"]


async def _reset(db) -> None:
    for name in RESET_COLLECTIONS:
        await db[name].delete_many({})


async def _seed(db, rng: random.Random) -> None:
    providers = []
    for data in PROVIDERS:
        providers.append(await products_repo.create_provider(db, {**data, "active": True}))

    products = []
    for index, (name, category, price, mayorista, cost, stock, min_stock) in enumerate(PRODUCTS):
        provider = providers[index % len(providers)]
        product = await products_repo.create_product(
            db,
            {
                "name": name,
                "category": category,
                "description": f"{name} tejido a mano en macramé.",
                "price": price,
                "price_mayorista": mayorista,
                "cost": cost,
                "stock": stock,
                "min_stock": min_stock,
                "unit": "unidad",
                "provider_id": ObjectId(str(provider.id)),
                "active": True,
            },
        )
        products.append(product)

    clients = []
    for name, client_type, phone, email, instagram, address, notes in CLIENTS:
        clients.append(
            await clients_repo.create_client(
                db,
                {
                    "name": name,
                    "type": client_type,
                    "phone": phone,
                    "email": email,
                    "instagram": instagram,
                    "address": address,
                    "notes": notes,
                    "active": True,
                },
            )
        )

    now = utcnow()
    sales_created = 0

    async def _create_order(client) -> None:
        nonlocal sales_created
        chosen = [p for p in rng.sample(products, k=rng.randint(1, 3)) if p.stock > 0]
        if not chosen:
            return
        sale_date = now - timedelta(days=rng.randint(0, 364), hours=rng.randint(0, 20))
        items = [
            SaleItemIn(product_id=str(product.id), qty=rng.randint(1, 4)) for product in chosen
        ]
        client_type = (
            client.type if client.type != "ambos" else rng.choice(["minorista", "mayorista"])
        )
        try:
            sale = await sales_service.create_sale(
                db,
                SaleCreate(
                    client_id=str(client.id),
                    client_type=client_type,
                    date=sale_date,
                    items=items,
                    shipping_cost=rng.choice([0, 0, 0, 1500, 2500]),
                    discount_pct=rng.choice([None, None, None, 5, 10]),
                ),
            )
        except Exception:
            return
        sales_created += 1

        status = rng.choice(STATUSES)
        if status != "cancelado" and rng.random() < 0.7:
            amount = int(sale.total * rng.choice([1.0, 1.0, 0.5, 0.3]))
            if amount > 0:
                await sales_service.add_payment(
                    db,
                    sale.id,
                    PaymentCreate(
                        amount=amount,
                        date=sale_date + timedelta(days=rng.randint(0, 10)),
                        type=rng.choice(["pago", "adelanto"]),
                        method=rng.choice(PAYMENT_METHODS),
                    ),
                )
        if status != "pendiente":
            await sales_service.update_sale(db, sale.id, SaleUpdate(status=status))

    for client in clients:
        await _create_order(client)
    for _ in range(48):
        await _create_order(rng.choice(clients))

    print(
        f"Seed listo: {len(providers)} proveedores, {len(products)} productos, "
        f"{len(clients)} clientes, {sales_created} órdenes."
    )


async def main() -> None:
    rng = random.Random(2026)
    await connect_db()
    db = await get_db()
    await _reset(db)
    await _seed(db, rng)
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
