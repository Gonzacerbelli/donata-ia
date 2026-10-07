async def _create_provider(auth_client, name="Proveedor SA"):
    r = await auth_client.post("/providers", json={"name": name})
    assert r.status_code == 201
    return r.json()


async def _create_product(auth_client, provider_id, **overrides):
    body = {
        "name": "Taza",
        "category": "vaviva",
        "price": 1000,
        "price_mayorista": 800,
        "cost": 500,
        "stock": 10,
        "min_stock": 2,
        "provider_id": provider_id,
    }
    body.update(overrides)
    return await auth_client.post("/products", json=body)


async def test_domain_routes_require_auth(client):
    assert (await client.get("/providers")).status_code == 401
    assert (await client.get("/products")).status_code == 401
    assert (await client.get("/clients")).status_code == 401
    assert (await client.get("/sales")).status_code == 401
    assert (await client.get("/reports/summary")).status_code == 401


async def test_provider_crud(auth_client):
    provider = await _create_provider(auth_client)
    listed = await auth_client.get("/providers")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    got = await auth_client.get(f"/providers/{provider['id']}")
    assert got.status_code == 200
    updated = await auth_client.patch(f"/providers/{provider['id']}", json={"contact": "Ana"})
    assert updated.status_code == 200
    assert updated.json()["contact"] == "Ana"
    deleted = await auth_client.delete(f"/providers/{provider['id']}")
    assert deleted.status_code == 204
    assert (await auth_client.get(f"/providers/{provider['id']}")).status_code == 404


async def test_product_crud(auth_client):
    provider = await _create_provider(auth_client)
    created = await _create_product(auth_client, provider["id"])
    assert created.status_code == 201
    product = created.json()
    assert product["stock"] == 10

    by_search = await auth_client.get("/products", params={"search": "Taza"})
    assert len(by_search.json()) == 1
    by_category = await auth_client.get("/products", params={"category": "vaviva"})
    assert len(by_category.json()) == 1
    by_provider = await auth_client.get("/products", params={"provider_id": provider["id"]})
    assert len(by_provider.json()) == 1

    updated = await auth_client.patch(f"/products/{product['id']}", json={"price": 1500})
    assert updated.json()["price"] == 1500

    deleted = await auth_client.delete(f"/products/{product['id']}")
    assert deleted.status_code == 204


async def test_product_requires_existing_provider(auth_client):
    bad = await _create_product(auth_client, "507f1f77bcf86cd799439011")
    assert bad.status_code == 422


async def test_delete_provider_with_products_conflict(auth_client):
    provider = await _create_provider(auth_client)
    await _create_product(auth_client, provider["id"])
    resp = await auth_client.delete(f"/providers/{provider['id']}")
    assert resp.status_code == 409


async def test_delete_product_with_sales_conflict(auth_client):
    provider = await _create_provider(auth_client)
    product = (await _create_product(auth_client, provider["id"])).json()
    client = await auth_client.post("/clients", json={"name": "C", "type": "minorista"})
    sale = await auth_client.post(
        "/sales",
        json={"client_id": client.json()["id"], "items": [{"product_id": product["id"], "qty": 1}]},
    )
    assert sale.status_code == 201
    resp = await auth_client.delete(f"/products/{product['id']}")
    assert resp.status_code == 409


async def test_stock_adjust_records_move(auth_client):
    provider = await _create_provider(auth_client)
    product = (await _create_product(auth_client, provider["id"])).json()
    resp = await auth_client.post(
        "/products/stock/adjust",
        json={"product_id": product["id"], "quantity": 5, "reason": "compra"},
    )
    assert resp.status_code == 200
    assert resp.json()["stock"] == 15
    moves = await auth_client.get(f"/products/{product['id']}/moves")
    assert moves.status_code == 200
    assert moves.json()[0]["quantity"] == 5
