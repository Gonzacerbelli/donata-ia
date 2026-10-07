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


async def test_load_tools_through_stdio_adapter():
    from app.services.llm.agent import load_tools

    tools = await load_tools()
    names = {tool.name for tool in tools}
    assert "crear_venta" in names
    assert "consultar_documentacion" in names
