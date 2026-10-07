async def _setup(auth_client):
    provider = (await auth_client.post("/providers", json={"name": "Prov"})).json()
    product = (
        await auth_client.post(
            "/products",
            json={
                "name": "Alfombra",
                "price": 1000,
                "cost": 400,
                "stock": 10,
                "min_stock": 20,
                "provider_id": provider["id"],
            },
        )
    ).json()
    client = (await auth_client.post("/clients", json={"name": "C"})).json()
    return product, client


async def test_reports_summary_and_top_products(auth_client):
    product, client = await _setup(auth_client)
    sale = (
        await auth_client.post(
            "/sales",
            json={"client_id": client["id"], "items": [{"product_id": product["id"], "qty": 2}]},
        )
    ).json()
    await auth_client.post(f"/sales/{sale['id']}/payments", json={"amount": 500})

    summary = (await auth_client.get("/reports/summary")).json()
    assert summary["sales_count"] == 1
    assert summary["revenue"] == 2000
    assert summary["collected"] == 500
    assert summary["receivable"] == 1500
    assert summary["average_ticket"] == 2000

    top = (await auth_client.get("/reports/top-products")).json()
    assert top[0]["description"] == "Alfombra"
    assert top[0]["qty"] == 2


async def test_reports_low_stock_and_inventory(auth_client):
    product, _ = await _setup(auth_client)
    low = (await auth_client.get("/reports/low-stock")).json()
    assert len(low) == 1
    assert low[0]["id"] == product["id"]

    inventory = (await auth_client.get("/reports/inventory-value")).json()
    assert inventory["units"] == 10
    assert inventory["inventory_value"] == 4000


async def test_canceled_sale_excluded_from_summary(auth_client):
    product, client = await _setup(auth_client)
    sale = (
        await auth_client.post(
            "/sales",
            json={"client_id": client["id"], "items": [{"product_id": product["id"], "qty": 1}]},
        )
    ).json()
    await auth_client.patch(f"/sales/{sale['id']}", json={"status": "cancelado"})
    summary = (await auth_client.get("/reports/summary")).json()
    assert summary["sales_count"] == 0
    assert summary["revenue"] == 0
