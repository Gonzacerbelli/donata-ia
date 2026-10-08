from datetime import UTC, datetime, timedelta

from app.models import utcnow
from app.repositories import sales as sales_repo
from app.services import notifications as notifications_service


async def _provider_and_product(auth_client, *, stock=20, min_stock=2, name="Taza"):
    provider = (await auth_client.post("/providers", json={"name": "Prov"})).json()
    product = (
        await auth_client.post(
            "/products",
            json={
                "name": name,
                "price": 1000,
                "cost": 500,
                "stock": stock,
                "min_stock": min_stock,
                "provider_id": provider["id"],
            },
        )
    ).json()
    return product


async def _client(auth_client, name="Ana"):
    return (await auth_client.post("/clients", json={"name": name, "type": "minorista"})).json()


async def _sale(auth_client, client_id, product_id, qty=1, **extra):
    body = {"client_id": client_id, "items": [{"product_id": product_id, "qty": qty}], **extra}
    response = await auth_client.post("/sales", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def _types(body):
    return {item["type"] for item in body["items"]}


def _item(body, notification_id):
    return next(item for item in body["items"] if item["id"] == notification_id)


async def test_stock_alerts(auth_client):
    await _provider_and_product(auth_client, stock=0, name="Agotada")
    await _provider_and_product(auth_client, stock=1, min_stock=5, name="Casi")

    body = (await auth_client.get("/notifications")).json()
    assert "STOCK_AGOTADO" in _types(body)
    assert "STOCK_MINIMO" in _types(body)
    agotado = next(i for i in body["items"] if i["type"] == "STOCK_AGOTADO")
    assert agotado["severity"] == "alta"
    assert agotado["entity"] == "product"


async def test_shipping_alerts(auth_client):
    product = await _provider_and_product(auth_client)
    client = await _client(auth_client)
    soon = (datetime.now(UTC) + timedelta(hours=10)).isoformat()
    past = (datetime.now(UTC) - timedelta(hours=10)).isoformat()
    await _sale(auth_client, client["id"], product["id"], ship_by=soon)
    await _sale(auth_client, client["id"], product["id"], ship_by=past)

    body = (await auth_client.get("/notifications")).json()
    assert "ENVIO_PENDIENTE" in _types(body)
    assert "ENVIO_VENCIDO" in _types(body)
    vencido = next(i for i in body["items"] if i["type"] == "ENVIO_VENCIDO")
    assert vencido["severity"] == "alta"


async def test_shipping_alert_absent_when_delivered(auth_client):
    product = await _provider_and_product(auth_client)
    client = await _client(auth_client)
    past = (datetime.now(UTC) - timedelta(hours=10)).isoformat()
    sale = await _sale(auth_client, client["id"], product["id"], ship_by=past)
    await auth_client.patch(f"/sales/{sale['id']}", json={"status": "entregado"})

    body = (await auth_client.get("/notifications")).json()
    ids = {i["id"] for i in body["items"]}
    assert f"ENVIO_VENCIDO:{sale['id']}" not in ids


async def test_payment_alerts(auth_client):
    product = await _provider_and_product(auth_client)
    client = await _client(auth_client)
    overdue = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    await _sale(auth_client, client["id"], product["id"], payment_due=overdue)
    await _sale(auth_client, client["id"], product["id"])

    body = (await auth_client.get("/notifications")).json()
    assert "PAGO_VENCIDO" in _types(body)
    assert "PAGO_PENDIENTE" in _types(body)


async def test_payment_alert_clears_when_paid(auth_client):
    product = await _provider_and_product(auth_client)
    client = await _client(auth_client)
    sale = await _sale(auth_client, client["id"], product["id"])
    await auth_client.post(f"/sales/{sale['id']}/payments", json={"amount": 1000})

    body = (await auth_client.get("/notifications")).json()
    ids = {i["id"] for i in body["items"]}
    assert f"PAGO_PENDIENTE:{sale['id']}" not in ids


async def test_payment_alert_absent_when_cancelled(auth_client):
    product = await _provider_and_product(auth_client)
    client = await _client(auth_client)
    sale = await _sale(auth_client, client["id"], product["id"])
    await auth_client.patch(f"/sales/{sale['id']}", json={"status": "cancelado"})

    body = (await auth_client.get("/notifications")).json()
    ids = {i["id"] for i in body["items"]}
    assert f"PAGO_PENDIENTE:{sale['id']}" not in ids
    assert f"PAGO_VENCIDO:{sale['id']}" not in ids


async def test_orden_sin_items_rule(db):
    sale = await sales_repo.create_sale(
        db,
        {
            "client_id": None,
            "client_type": "minorista",
            "date": utcnow(),
            "items": [],
            "subtotal": 0,
            "total": 0,
            "status": "pendiente",
            "payments": [],
            "created_at": utcnow(),
            "updated_at": utcnow(),
        },
    )
    alerts = await notifications_service.compute_alerts(db)
    ids = {a["id"] for a in alerts}
    assert f"ORDEN_SIN_ITEMS:{sale.id}" in ids
    alert = next(a for a in alerts if a["type"] == "ORDEN_SIN_ITEMS")
    assert alert["severity"] == "baja"


async def test_read_and_dismiss_state(auth_client):
    await _provider_and_product(auth_client, stock=0, name="Agotada")
    body = (await auth_client.get("/notifications")).json()
    assert body["unread_count"] >= 1
    target = body["items"][0]["id"]

    marked = await auth_client.patch(f"/notifications/{target}", json={"read": True})
    updated = marked.json()
    assert _item(updated, target)["read"] is True
    assert updated["unread_count"] == body["unread_count"] - 1

    dismissed = await auth_client.patch(f"/notifications/{target}", json={"dismissed": True})
    remaining = {i["id"] for i in dismissed.json()["items"]}
    assert target not in remaining


async def test_read_all_clears_unread(auth_client):
    await _provider_and_product(auth_client, stock=0)
    response = await auth_client.post("/notifications/read-all")
    assert response.status_code == 200
    assert response.json()["unread_count"] == 0


async def test_dismiss_all_empties_panel(auth_client):
    await _provider_and_product(auth_client, stock=0)
    response = await auth_client.post("/notifications/dismiss-all")
    assert response.status_code == 200
    assert response.json()["items"] == []


async def test_update_unknown_notification_404(auth_client):
    response = await auth_client.patch("/notifications/STOCK_AGOTADO:missing", json={"read": True})
    assert response.status_code == 404
