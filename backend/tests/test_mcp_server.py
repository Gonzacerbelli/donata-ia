from app.mcp_server import mcp

EXPECTED_TOOLS = {
    "buscar_productos",
    "buscar_productos_semantico",
    "consultar_producto",
    "consultar_precios",
    "listar_clientes",
    "crear_cliente",
    "listar_ventas",
    "crear_venta",
    "registrar_pago",
    "cancelar_venta",
    "reponer_stock",
    "resumen_negocio",
    "consultar_documentacion",
}


async def test_mcp_exposes_business_tools():
    tools = await mcp.get_tools()
    assert EXPECTED_TOOLS.issubset(set(tools))


async def test_mcp_tool_creates_client(db):
    from app.mcp_server import crear_cliente, listar_clientes

    created = await crear_cliente.fn(nombre="Cliente MCP", tipo="mayorista")
    assert created["name"] == "Cliente MCP"
    listed = await listar_clientes.fn(query="MCP")
    assert any(c["id"] == created["id"] for c in listed)


async def test_mcp_crear_cliente_guarda_telefono_y_direccion(db):
    from app.mcp_server import crear_cliente, listar_clientes

    created = await crear_cliente.fn(
        nombre="Marta MCP",
        telefono="1165245400",
        direccion="Avenida Libertador 312, Córdoba",
    )
    assert created["phone"] == "1165245400"
    assert created["address"] == "Avenida Libertador 312, Córdoba"

    listed = await listar_clientes.fn(query="Marta MCP")
    assert listed[0]["address"] == "Avenida Libertador 312, Córdoba"


async def test_mcp_crear_venta_registra_sena_notas_y_stock(db):
    from bson import ObjectId

    from app.mcp_server import buscar_productos, crear_cliente, crear_venta
    from app.repositories import products as products_repo

    provider = await products_repo.create_provider(db, {"name": "Proveedor MCP", "active": True})
    product = await products_repo.create_product(
        db,
        {
            "name": "Soporte para plantas trípode",
            "category": "accesorios",
            "price": 1000,
            "cost": 500,
            "stock": 10,
            "min_stock": 1,
            "unit": "unidad",
            "provider_id": ObjectId(str(provider.id)),
            "active": True,
        },
    )
    client = await crear_cliente.fn(nombre="Marta Venta MCP")

    sale = await crear_venta.fn(
        cliente_id=client["id"],
        items=[{"product_id": str(product.id), "qty": 7}],
        envio=500,
        notas="Envío por Andreani",
        pago_porcentaje=50,
    )
    assert sale["total"] == 7500
    assert sale["notes"] == "Envío por Andreani"
    assert sale["payments"][0]["type"] == "adelanto"
    assert sale["payments"][0]["amount"] == 3750
    assert sale["status"] == "pendiente"

    listed = await buscar_productos.fn(query="trípode")
    assert listed[0]["stock"] == 3

    import pytest

    with pytest.raises(ValueError):
        await crear_venta.fn(
            cliente_id=client["id"],
            items=[{"product_id": str(product.id), "qty": 1}],
            pago_monto=99999,
        )

    listed = await buscar_productos.fn(query="trípode")
    assert listed[0]["stock"] == 3


async def test_load_tools_through_stdio_adapter():
    from app.services.llm.agent import load_tools

    tools = await load_tools()
    names = {tool.name for tool in tools}
    assert "crear_venta" in names
    assert "consultar_documentacion" in names
    assert "reponer_stock" in names


async def test_mcp_reponer_stock_suma_unidades_y_actualiza_precio(db):
    import pytest

    from app.mcp_server import buscar_productos, reponer_stock
    from app.repositories import products as products_repo
    from app.services import stock as stock_service

    provider = await products_repo.create_provider(
        db, {"name": "Proveedor Reposición", "active": True}
    )
    product = await products_repo.create_product(
        db,
        {
            "name": "Cortina de macramé",
            "category": "decoracion",
            "price": 30000,
            "cost": 18000,
            "stock": 3,
            "min_stock": 2,
            "unit": "unidad",
            "provider_id": provider.id,
            "active": True,
        },
    )

    updated = await reponer_stock.fn(producto_id=str(product.id), cantidad=10, precio_venta=35000)
    assert updated["stock"] == 13
    assert updated["price"] == 35000

    listed = await buscar_productos.fn(query="Cortina de macramé")
    assert listed[0]["stock"] == 13
    assert listed[0]["price"] == 35000

    moves = await stock_service.list_moves(db, str(product.id))
    assert moves[-1].quantity == 10
    assert moves[-1].reason == "reposición"

    solo_precio = await reponer_stock.fn(producto_id=str(product.id), precio_venta=36000)
    assert solo_precio["stock"] == 13
    assert solo_precio["price"] == 36000

    with pytest.raises(ValueError):
        await reponer_stock.fn(producto_id=str(product.id))
    with pytest.raises(ValueError):
        await reponer_stock.fn(producto_id=str(product.id), cantidad=-2)
