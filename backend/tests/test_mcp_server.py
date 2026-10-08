from app.mcp_server import mcp

EXPECTED_TOOLS = {
    "buscar_productos",
    "buscar_productos_semantico",
    "listar_productos_a_reponer",
    "consultar_producto",
    "consultar_precios",
    "listar_clientes",
    "crear_cliente",
    "listar_ventas",
    "consultar_saldo_cliente",
    "listar_clientes_pendientes",
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


async def test_mcp_listar_productos_a_reponer_devuelve_solo_bajo_minimo(db):
    from bson import ObjectId

    from app.mcp_server import listar_productos_a_reponer
    from app.repositories import products as products_repo

    provider = await products_repo.create_provider(
        db, {"name": "Proveedor Reposición", "active": True}
    )
    provider_id = ObjectId(str(provider.id))

    async def _create(name, stock, min_stock, active=True):
        await products_repo.create_product(
            db,
            {
                "name": name,
                "category": "accesorios",
                "price": 1000,
                "cost": 500,
                "stock": stock,
                "min_stock": min_stock,
                "unit": "unidad",
                "provider_id": provider_id,
                "active": active,
            },
        )

    await _create("Producto agotado", 0, 3)
    await _create("Producto justo", 3, 3)
    await _create("Producto de sobra", 10, 3)
    await _create("Producto inactivo", 0, 3, active=False)

    reponer = await listar_productos_a_reponer.fn()
    nombres = {p["nombre"] for p in reponer}

    assert "Producto agotado" in nombres
    assert "Producto justo" in nombres
    assert "Producto de sobra" not in nombres
    assert "Producto inactivo" not in nombres
    assert all(set(p) == {"nombre", "stock", "minimo", "unidad"} for p in reponer)
    assert [p["stock"] for p in reponer] == sorted(p["stock"] for p in reponer)


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


async def _seed_cliente_con_ventas(db):
    from bson import ObjectId

    from app.mcp_server import cancelar_venta, crear_cliente, crear_venta
    from app.repositories import products as products_repo

    provider = await products_repo.create_provider(db, {"name": "Proveedor Saldo", "active": True})
    product = await products_repo.create_product(
        db,
        {
            "name": "Alfombra de prueba saldo",
            "category": "alfombras",
            "price": 1000,
            "cost": 500,
            "stock": 50,
            "min_stock": 1,
            "unit": "unidad",
            "provider_id": ObjectId(str(provider.id)),
            "active": True,
        },
    )
    client = await crear_cliente.fn(nombre="Cliente Saldo MCP")
    await crear_venta.fn(
        cliente_id=client["id"],
        items=[{"product_id": str(product.id), "qty": 7}],
        envio=500,
        pago_porcentaje=50,
    )
    cancelada = await crear_venta.fn(
        cliente_id=client["id"], items=[{"product_id": str(product.id), "qty": 1}]
    )
    await cancelar_venta.fn(venta_id=cancelada["id"])
    return client


async def test_mcp_listas_aceptan_nulls_como_vacios(db):
    from app.mcp_server import listar_clientes, listar_ventas

    assert isinstance(await listar_clientes.fn(query=None, tipo=None), list)
    assert isinstance(await listar_ventas.fn(estado=None, cliente_id=None, limite=None), list)


async def test_mcp_consultar_saldo_cliente_excluye_canceladas(db):
    from app.mcp_server import consultar_saldo_cliente

    client = await _seed_cliente_con_ventas(db)
    saldo = await consultar_saldo_cliente.fn(cliente=client["id"])
    assert saldo["cliente"]["nombre"] == "Cliente Saldo MCP"
    assert saldo["ordenes"] == 2
    assert saldo["canceladas"] == 1
    assert saldo["facturado"] == 7500
    assert saldo["cobrado"] == 3750
    assert saldo["deuda"] == 3750
    assert saldo["saldo_cancelado"] == 1000
    assert {o["se_cuenta"] for o in saldo["detalle"]} == {True, False}
    assert {o["saldo"] for o in saldo["detalle"]} == {3750, 1000}

    por_nombre = await consultar_saldo_cliente.fn(cliente="Cliente Saldo MCP")
    assert por_nombre["deuda"] == 3750

    assert "error" in await consultar_saldo_cliente.fn(cliente=None)
    assert "error" in await consultar_saldo_cliente.fn(cliente="507f1f77bcf86cd799439011")


async def test_mcp_listar_clientes_pendientes_agrupa_sin_canceladas(db):
    from app.mcp_server import listar_clientes_pendientes

    await _seed_cliente_con_ventas(db)
    rows = await listar_clientes_pendientes.fn()
    row = next(r for r in rows if r["nombre"] == "Cliente Saldo MCP")
    assert row["ordenes_pendientes"] == 1
    assert row["saldo"] == 3750
    assert row["tipo"] == "minorista"
    assert rows == sorted(rows, key=lambda r: r["saldo"], reverse=True)
