async def _setup(auth_client):
    provider = (await auth_client.post("/providers", json={"name": "Prov"})).json()
    product = (
        await auth_client.post(
            "/products",
            json={
                "name": "Alfombra",
                "price": 1000,
                "price_mayorista": 800,
                "cost": 400,
                "stock": 10,
                "min_stock": 1,
                "provider_id": provider["id"],
            },
        )
    ).json()
    minor = (await auth_client.post("/clients", json={"name": "Minor", "type": "minorista"})).json()
    mayor = (await auth_client.post("/clients", json={"name": "Mayor", "type": "mayorista"})).json()
    return product, minor, mayor


async def _stock(auth_client, product_id):
    return (await auth_client.get(f"/products/{product_id}")).json()["stock"]


async def test_create_sale_minorista_pricing_and_stock(auth_client):
    product, minor, _ = await _setup(auth_client)
    resp = await auth_client.post(
        "/sales",
        json={"client_id": minor["id"], "items": [{"product_id": product["id"], "qty": 2}]},
    )
    assert resp.status_code == 201
    sale = resp.json()
    assert sale["items"][0]["unit_price"] == 1000
    assert sale["subtotal"] == 2000
    assert sale["total"] == 2000
    assert sale["status"] == "pendiente"
    assert await _stock(auth_client, product["id"]) == 8


async def test_create_sale_mayorista_uses_wholesale_price(auth_client):
    product, _, mayor = await _setup(auth_client)
    resp = await auth_client.post(
        "/sales",
        json={"client_id": mayor["id"], "items": [{"product_id": product["id"], "qty": 1}]},
    )
    assert resp.json()["items"][0]["unit_price"] == 800


async def test_create_sale_with_discount_pct(auth_client):
    product, minor, _ = await _setup(auth_client)
    resp = await auth_client.post(
        "/sales",
        json={
            "client_id": minor["id"],
            "items": [{"product_id": product["id"], "qty": 1}],
            "discount_pct": 10,
            "shipping_cost": 500,
        },
    )
    sale = resp.json()
    assert sale["discount"] == 100
    assert sale["total"] == 1000 - 100 + 500


async def test_create_sale_mixed_items(auth_client):
    product, minor, _ = await _setup(auth_client)
    resp = await auth_client.post(
        "/sales",
        json={
            "client_id": minor["id"],
            "items": [
                {"product_id": product["id"], "qty": 1},
                {"description": "Servicio de colocación", "qty": 1, "unit_price": 3000},
            ],
        },
    )
    sale = resp.json()
    assert sale["subtotal"] == 4000
    descriptions = {item["description"] for item in sale["items"]}
    assert "Servicio de colocación" in descriptions


async def test_insufficient_stock_rolls_back(auth_client):
    product, minor, _ = await _setup(auth_client)
    resp = await auth_client.post(
        "/sales",
        json={"client_id": minor["id"], "items": [{"product_id": product["id"], "qty": 99}]},
    )
    assert resp.status_code == 400
    assert await _stock(auth_client, product["id"]) == 10
    sales = await auth_client.get("/sales")
    assert sales.json() == []


async def test_cancel_restores_and_reactivate_removes_stock(auth_client):
    product, minor, _ = await _setup(auth_client)
    sale = (
        await auth_client.post(
            "/sales",
            json={"client_id": minor["id"], "items": [{"product_id": product["id"], "qty": 3}]},
        )
    ).json()
    assert await _stock(auth_client, product["id"]) == 7

    cancelled = await auth_client.patch(f"/sales/{sale['id']}", json={"status": "cancelado"})
    assert cancelled.status_code == 200
    assert await _stock(auth_client, product["id"]) == 10

    reactivated = await auth_client.patch(f"/sales/{sale['id']}", json={"status": "en_proceso"})
    assert reactivated.status_code == 200
    assert await _stock(auth_client, product["id"]) == 7


async def test_payments_and_balance(auth_client):
    product, minor, _ = await _setup(auth_client)
    sale = (
        await auth_client.post(
            "/sales",
            json={"client_id": minor["id"], "items": [{"product_id": product["id"], "qty": 2}]},
        )
    ).json()
    paid = await auth_client.post(
        f"/sales/{sale['id']}/payments", json={"amount": 1500, "type": "adelanto"}
    )
    body = paid.json()
    assert body["paid"] == 1500
    assert body["balance"] == 500


async def test_payment_on_canceled_sale_is_rejected(auth_client):
    product, minor, _ = await _setup(auth_client)
    sale = (
        await auth_client.post(
            "/sales",
            json={"client_id": minor["id"], "items": [{"product_id": product["id"], "qty": 1}]},
        )
    ).json()
    await auth_client.patch(f"/sales/{sale['id']}", json={"status": "cancelado"})
    resp = await auth_client.post(f"/sales/{sale['id']}/payments", json={"amount": 100})
    assert resp.status_code == 400


async def test_delete_sale_with_payments_conflict(auth_client):
    product, minor, _ = await _setup(auth_client)
    sale = (
        await auth_client.post(
            "/sales",
            json={"client_id": minor["id"], "items": [{"product_id": product["id"], "qty": 1}]},
        )
    ).json()
    await auth_client.post(f"/sales/{sale['id']}/payments", json={"amount": 100})
    resp = await auth_client.delete(f"/sales/{sale['id']}")
    assert resp.status_code == 409


async def test_delete_sale_restores_stock(auth_client):
    product, minor, _ = await _setup(auth_client)
    sale = (
        await auth_client.post(
            "/sales",
            json={"client_id": minor["id"], "items": [{"product_id": product["id"], "qty": 4}]},
        )
    ).json()
    assert await _stock(auth_client, product["id"]) == 6
    resp = await auth_client.delete(f"/sales/{sale['id']}")
    assert resp.status_code == 204
    assert await _stock(auth_client, product["id"]) == 10


async def test_delete_client_with_sales_conflict(auth_client):
    product, minor, _ = await _setup(auth_client)
    await auth_client.post(
        "/sales",
        json={"client_id": minor["id"], "items": [{"product_id": product["id"], "qty": 1}]},
    )
    resp = await auth_client.delete(f"/clients/{minor['id']}")
    assert resp.status_code == 409


async def test_sale_with_unknown_client_404(auth_client):
    product, _, _ = await _setup(auth_client)
    resp = await auth_client.post(
        "/sales",
        json={
            "client_id": "507f1f77bcf86cd799439011",
            "items": [{"product_id": product["id"], "qty": 1}],
        },
    )
    assert resp.status_code == 404
