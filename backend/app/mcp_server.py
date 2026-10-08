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
