"""Servidor MCP de Donata (transporte stdio).

Expone herramientas de negocio en español que envuelven los servicios de la
aplicación. Se ejecuta como proceso hijo del agente:

    python -m app.mcp_server
"""

from fastmcp import FastMCP

from app.db import get_db
from app.repositories import clients as clients_repo
from app.repositories import products as products_repo
from app.repositories import sales as sales_repo
from app.schemas.entities import (
    ClientCreate,
    PaymentCreate,
    SaleCreate,
    SaleUpdate,
)
from app.services import clients as clients_service
from app.services import products as products_service
from app.services import reports as reports_service
from app.services import sales as sales_service
from app.services.llm import rag as rag_service
from app.services.llm import vector_store

mcp = FastMCP("donata-mcp")


def _product_dict(product) -> dict:
    return product.model_dump(mode="json")


@mcp.tool()
async def buscar_productos(
    query: str = "", categoria: str = "", solo_con_stock: bool = False
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
async def buscar_productos_semantico(query: str, limite: int = 5) -> list[dict]:
    """Busca productos por significado (búsqueda semántica), ideal para descripciones difusas."""
    documents = vector_store.search_products_semantic(query, k=limite)
    return [{"contenido": d.page_content, **d.metadata} for d in documents]


@mcp.tool()
async def consultar_producto(producto_id: str) -> dict:
    """Devuelve el detalle y el stock de un producto por su id."""
    db = await get_db()
    product = await products_service.get_product_or_404(db, producto_id)
    return _product_dict(product)


@mcp.tool()
async def consultar_precios(producto: str, tipo_cliente: str = "minorista") -> list[dict]:
    """Consulta precios minorista y mayorista de los productos que coinciden con el texto."""
    db = await get_db()
    products = await products_repo.list_products(db, search=producto, active_only=True)
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
async def listar_clientes(query: str = "", tipo: str = "") -> list[dict]:
    """Lista o busca clientes por nombre, teléfono o Instagram."""
    db = await get_db()
    clients = await clients_repo.list_clients(db, search=query or None, client_type=tipo or None)
    return [c.model_dump(mode="json") for c in clients]


@mcp.tool()
async def crear_cliente(
    nombre: str, telefono: str = "", email: str = "", tipo: str = "minorista"
) -> dict:
    """Crea un cliente nuevo."""
    db = await get_db()
    body = ClientCreate(name=nombre, phone=telefono or None, email=email or None, type=tipo)
    client = await clients_service.create_client(db, body)
    return client.model_dump(mode="json")


@mcp.tool()
async def listar_ventas(estado: str = "", cliente_id: str = "", limite: int = 20) -> list[dict]:
    """Lista ventas, filtrando por estado o cliente."""
    db = await get_db()
    sales = await sales_repo.list_sales(db, status=estado or None, client_id=cliente_id or None)
    return [s.model_dump(mode="json") for s in sales[:limite]]


@mcp.tool()
async def crear_venta(
    cliente_id: str,
    items: list[dict],
    descuento: int = 0,
    envio: int = 0,
    tipo_cliente: str = "",
) -> dict:
    """Registra una venta. Cada ítem admite product_id+qty o description+qty+unit_price."""
    db = await get_db()
    body = SaleCreate(
        client_id=cliente_id,
        items=items,
        discount=descuento,
        shipping_cost=envio,
        client_type=tipo_cliente or None,
    )
    sale = await sales_service.create_sale(db, body)
    return sale.model_dump(mode="json")


@mcp.tool()
async def registrar_pago(venta_id: str, monto: int, tipo: str = "pago") -> dict:
    """Registra un pago o adelanto sobre una venta."""
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
async def resumen_negocio(desde: str = "", hasta: str = "") -> dict:
    """Devuelve métricas del negocio: ventas, facturación, cobrado y por cobrar."""
    db = await get_db()
    return await reports_service.sales_summary(db, date_from=desde or None, date_to=hasta or None)


@mcp.tool()
async def consultar_documentacion(pregunta: str) -> str:
    """Responde preguntas sobre las reglas y el funcionamiento del negocio (manual operativo)."""
    return await rag_service.answer_question_async(pregunta)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
