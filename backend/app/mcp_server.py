"""Servidor MCP de Donata (transporte stdio).

Expone herramientas de negocio en español que envuelven los servicios de la
aplicación. Se ejecuta como proceso hijo del agente:

    python -m app.mcp_server
"""

from typing import Literal

from fastmcp import FastMCP

from app.db import get_db
from app.repositories import clients as clients_repo
from app.repositories import products as products_repo
from app.repositories import sales as sales_repo
from app.schemas.entities import (
    ClientCreate,
    PaymentCreate,
    ProductUpdate,
    SaleCreate,
    SaleUpdate,
)
from app.services import clients as clients_service
from app.services import products as products_service
from app.services import reports as reports_service
from app.services import sales as sales_service
from app.services import stock as stock_service
from app.services.llm import rag as rag_service
from app.services.llm import vector_store

mcp = FastMCP("donata-mcp")


def _product_dict(product) -> dict:
    return product.model_dump(mode="json")


@mcp.tool()
async def buscar_productos(
    query: str | None = "", categoria: str | None = "", solo_con_stock: bool | None = False
) -> list[dict]:
    """Busca productos del catálogo por texto o categoría."""
    db = await get_db()
    products = await products_repo.list_products(
        db,
        search=query or None,
        category=categoria or None,
        active_only=True,
    )
    if solo_con_stock:
        products = [p for p in products if p.stock > 0]
    return [_product_dict(p) for p in products]


@mcp.tool()
async def listar_productos_a_reponer() -> list[dict]:
    """Productos con stock en el mínimo o por debajo: hay que reponerlos.

    Usá esta herramienta de UNA sola vez para "qué productos debo reponer", "qué falta
    reponer", "stock bajo" o "qué se está por agotar". Devuelve `nombre`, `stock`,
    `minimo` y `unidad` de cada producto. Nunca pidas ids: respondé con los nombres.
    """
    db = await get_db()
    products = await products_repo.list_products(db, active_only=True)
    bajos = [p for p in products if p.stock <= p.min_stock]
    bajos.sort(key=lambda p: p.stock)
    return [
        {"nombre": p.name, "stock": p.stock, "minimo": p.min_stock, "unidad": p.unit} for p in bajos
    ]


@mcp.tool()
async def buscar_productos_semantico(query: str | None = "", limite: int | None = 5) -> list[dict]:
    """Busca productos por significado (búsqueda semántica), ideal para descripciones difusas."""
    if not query:
        return [{"error": "Falta la búsqueda: pasá `query` con lo que buscás."}]
    documents = vector_store.search_products_semantic(query, k=limite or 5)
    return [{"contenido": d.page_content, **d.metadata} for d in documents]


@mcp.tool()
async def consultar_producto(producto_id: str | None = "") -> dict:
    """Devuelve el detalle y el stock de un producto por su id."""
    if not producto_id:
        return {"error": "Falta el id del producto: pasá `producto_id`."}
    db = await get_db()
    product = await products_service.get_product_or_404(db, producto_id)
    return _product_dict(product)


@mcp.tool()
async def consultar_precios(
    producto: str | None = "", tipo_cliente: str | None = "minorista"
) -> list[dict]:
    """Consulta precios minorista y mayorista de los productos que coinciden con el texto."""
    db = await get_db()
    products = await products_repo.list_products(db, search=producto or None, active_only=True)
    result = []
    for p in products:
        price = (
            p.price_mayorista if (tipo_cliente == "mayorista" and p.price_mayorista) else p.price
        )
        result.append(
            {
                "id": str(p.id),
                "nombre": p.name,
                "precio_minorista": p.price,
                "precio_mayorista": p.price_mayorista,
                "precio_aplicado": price,
                "stock": p.stock,
            }
        )
    return result


@mcp.tool()
async def listar_clientes(query: str | None = "", tipo: str | None = "") -> list[dict]:
    """Lista o busca clientes por nombre, teléfono o Instagram."""
    db = await get_db()
    clients = await clients_repo.list_clients(db, search=query or None, client_type=tipo or None)
    return [c.model_dump(mode="json") for c in clients]


@mcp.tool()
async def crear_cliente(
    nombre: str,
    telefono: str = "",
    email: str = "",
    direccion: str = "",
    tipo: Literal["minorista", "mayorista", "ambos"] = "minorista",
    notas: str = "",
) -> dict:
    """Crea un cliente nuevo. Pasá `direccion` (domicilio de entrega) y `telefono` si los tenés."""
    db = await get_db()
    body = ClientCreate(
        name=nombre,
        phone=telefono or None,
        email=email or None,
        address=direccion or None,
        type=tipo,
        notes=notas or None,
    )
    client = await clients_service.create_client(db, body)
    return client.model_dump(mode="json")


@mcp.tool()
async def listar_ventas(
    estado: str | None = "", cliente_id: str | None = "", limite: int | None = 20
) -> list[dict]:
    """Lista ventas, filtrando por estado o cliente. `limite` por defecto es 20."""
    db = await get_db()
    resolved = cliente_id or None
    if cliente_id:
        client = await _resolve_client(db, cliente_id)
        if client is not None:
            resolved = str(client.id)
    sales = await sales_repo.list_sales(db, status=estado or None, client_id=resolved)
    return [s.model_dump(mode="json") for s in sales[: limite or 20]]


async def _resolve_client(db, value: str | None):
    """Resuelve un cliente por id o, si el valor no es un id válido, por nombre.

    Tolerante a que el modelo pase el nombre en lugar del id: primero intenta el id,
    y si no lo encuentra busca por nombre (coincidencia por subcadena, sin distinguir
    mayúsculas). Devuelve el `Client` o None.
    """
    if not value:
        return None
    client = await clients_repo.get_client(db, value)
    if client is not None:
        return client
    matches = await clients_repo.list_clients(db, search=value)
    return matches[0] if matches else None


@mcp.tool()
async def consultar_saldo_cliente(cliente: str | None = "") -> dict:
    """Saldo de un cliente con los totales YA calculados: órdenes, facturado, cobrado y deuda.

    Usá esta herramienta para "cuánto debe", "saldo" o "deuda" de un cliente: no sumes
    los montos a mano. Pasá en `cliente` el NOMBRE del cliente (por ejemplo "Casa & Estilo");
    la herramienta lo resuelve sola, no necesitás buscar antes su id. También acepta el id.
    Las órdenes canceladas se listan en `detalle`, pero NO se suman ni en `deuda` ni en
    `facturado`: una orden cancelada no debe dinero. `saldo_cancelado` es el monto que
    quedó en canceladas, sólo informativo.
    """
    if not cliente:
        return {"error": "Falta el cliente: pasá su nombre o id en `cliente`."}
    db = await get_db()
    client = await _resolve_client(db, cliente)
    if client is None:
        return {"error": f"No existe un cliente con id o nombre '{cliente}'."}
    sales = await sales_repo.list_sales(db, client_id=str(client.id))
    orders = sorted(
        (s.model_dump(mode="json") for s in sales), key=lambda s: s["date"], reverse=True
    )
    activas = [s for s in orders if s["status"] != "cancelado"]
    return {
        "cliente": {"id": str(client.id), "nombre": client.name},
        "ordenes": len(orders),
        "canceladas": len(orders) - len(activas),
        "facturado": sum(s["total"] for s in activas),
        "cobrado": sum(s["paid"] for s in activas),
        "deuda": sum(s["balance"] for s in activas),
        "saldo_cancelado": sum(s["balance"] for s in orders if s["status"] == "cancelado"),
        "detalle": [
            {
                "fecha": s["date"][:10],
                "estado": s["status"],
                "total": s["total"],
                "pagado": s["paid"],
                "saldo": s["balance"],
                "se_cuenta": s["status"] != "cancelado",
            }
            for s in orders
        ],
    }


@mcp.tool()
async def listar_clientes_pendientes() -> list[dict]:
    """Clientes con órdenes sin entregar que todavía deben plata.

    Usá esta herramienta de UNA sola llamada para "clientes con pedidos pendientes",
    "quién no le entregamos", "pendientes de pago" u "órdenes sin entregar". Devuelve
    el `nombre` de cada cliente, su `tipo`, la cantidad de órdenes `ordenes_pendientes`
    (estado pendiente o en_proceso con saldo > 0) y el `saldo` ya sumado: no iteres
    cliente por cliente ni sumes montos a mano. Las canceladas no cuentan. Respondé
    siempre con los nombres, nunca con ids.
    """
    db = await get_db()
    sales = await sales_repo.list_sales(db)
    deudores: dict[str, dict] = {}
    for sale in sales:
        if sale.status not in ("pendiente", "en_proceso") or sale.balance <= 0:
            continue
        row = deudores.setdefault(str(sale.client_id), {"ordenes_pendientes": 0, "saldo": 0})
        row["ordenes_pendientes"] += 1
        row["saldo"] += sale.balance
    result: list[dict] = []
    for client_id, totals in deudores.items():
        client = await clients_repo.get_client(db, client_id)
        if client is None:
            continue
        result.append(
            {
                "nombre": client.name,
                "tipo": client.type,
                "ordenes_pendientes": totals["ordenes_pendientes"],
                "saldo": totals["saldo"],
            }
        )
    result.sort(key=lambda row: row["saldo"], reverse=True)
    return result


@mcp.tool()
async def crear_venta(
    cliente_id: str,
    items: list[dict],
    descuento: int = 0,
    envio: int = 0,
    tipo_cliente: Literal["", "minorista", "mayorista"] = "",
    notas: str = "",
    pago_porcentaje: float = 0,
    pago_monto: int = 0,
    pago_tipo: Literal["adelanto", "pago"] = "adelanto",
    pago_metodo: str = "",
) -> dict:
    """Registra una venta y, si lo pedís, su primer pago en la misma operación.

    - items: [{"product_id": "<id>", "qty": 7}] o
      [{"description": "...", "qty": 7, "unit_price": n}].
    - envio: costo de envío en pesos enteros.
      notas: detalle libre, p. ej. "Envío por Andreani".
    - pago_porcentaje (0-100) o pago_monto (pesos) registran la seña al crear la venta;
      pago_tipo es "adelanto" (seña) o "pago" (cobro total) y pago_metodo p. ej. "Efectivo".
    """
    db = await get_db()
    body = SaleCreate(
        client_id=cliente_id,
        items=items,
        discount=descuento,
        shipping_cost=envio,
        client_type=tipo_cliente or None,
        notes=notas or None,
    )
    sale = await sales_service.create_sale(db, body)
    monto = int(pago_monto)
    if monto <= 0 and pago_porcentaje:
        monto = round(sale.total * float(pago_porcentaje) / 100)
    if monto > sale.total:
        await sales_service.delete_sale(db, sale.id)
        raise ValueError(
            f"El pago inicial ({monto}) no puede superar el total de la venta ({sale.total})"
        )
    if monto > 0:
        sale = await sales_service.add_payment(
            db,
            sale.id,
            PaymentCreate(amount=monto, type=pago_tipo, method=pago_metodo or None),
        )
    return sale.model_dump(mode="json")


@mcp.tool()
async def registrar_pago(
    venta_id: str, monto: int, tipo: Literal["adelanto", "pago"] = "pago"
) -> dict:
    """Registra un pago sobre una venta existente: `tipo` "adelanto" (seña) o "pago" (saldo)."""
    db = await get_db()
    sale = await sales_service.add_payment(db, venta_id, PaymentCreate(amount=monto, type=tipo))
    return sale.model_dump(mode="json")


@mcp.tool()
async def cancelar_venta(venta_id: str) -> dict:
    """Cancela una venta y restituye el stock de sus productos."""
    db = await get_db()
    sale = await sales_service.update_sale(db, venta_id, SaleUpdate(status="cancelado"))
    return sale.model_dump(mode="json")


@mcp.tool()
async def reponer_stock(producto_id: str, cantidad: int = 0, precio_venta: int = 0) -> dict:
    """Suma stock a un producto y/o actualiza su precio de venta.

    - producto_id: id del producto (buscalo con `buscar_productos` o `consultar_producto`).
    - cantidad: unidades a sumar al stock (0 si sólo cambia el precio).
    - precio_venta: nuevo precio minorista en pesos enteros (0 = no cambiar).
    """
    db = await get_db()
    if cantidad < 0 or precio_venta < 0:
        raise ValueError("La cantidad y el precio de venta no pueden ser negativos")
    if cantidad == 0 and precio_venta == 0:
        raise ValueError("Indicá la cantidad a reponer, el precio de venta o ambos")
    product = await products_service.get_product_or_404(db, producto_id)
    if cantidad:
        product = await stock_service.adjust_stock(db, producto_id, cantidad, reason="reposición")
    if precio_venta:
        product = await products_service.update_product(
            db, producto_id, ProductUpdate(price=int(precio_venta))
        )
    return _product_dict(product)


@mcp.tool()
async def resumen_negocio(desde: str | None = "", hasta: str | None = "") -> dict:
    """Devuelve métricas del negocio: ventas, facturación, cobrado y por cobrar."""
    db = await get_db()
    return await reports_service.sales_summary(db, date_from=desde or None, date_to=hasta or None)


@mcp.tool()
async def consultar_documentacion(pregunta: str | None = "") -> str:
    """Responde preguntas sobre las reglas y el funcionamiento del negocio (manual operativo)."""
    if not pregunta:
        return "Falta la pregunta: pasá `pregunta` con tu duda sobre el funcionamiento del negocio."
    return await rag_service.answer_question_async(pregunta)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
