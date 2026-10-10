from app.models import utcnow
from app.repositories import users as users_repo
from app.repositories.base import valid_oid


async def _setup(auth_client):
    provider = (await auth_client.post("/providers", json={"name": "Prov"})).json()
    product = (
        await auth_client.post(
            "/products",
            json={"name": "Alfombra", "price": 1000, "stock": 10, "provider_id": provider["id"]},
        )
    ).json()
    client = (
        await auth_client.post("/clients", json={"name": "Clienta", "type": "minorista"})
    ).json()
    sale = (
        await auth_client.post(
            "/sales",
            json={"client_id": client["id"], "items": [{"product_id": product["id"], "qty": 2}]},
        )
    ).json()
    return product, client, sale


async def _board(auth_client, **params):
    query = "&".join(f"{key}={value}" for key, value in params.items() if value is not None)
    path = f"/work-items?{query}" if query else "/work-items"
    return (await auth_client.get(path)).json()


async def test_board_lists_non_cancelled_with_defaults(auth_client):
    _, _, sale = await _setup(auth_client)
    board = await _board(auth_client)
    assert len(board) == 1
    card = board[0]
    assert card["sale_id"] == sale["id"]
    assert card["status"] == "pendiente"
    assert card["priority"] == "media"
    assert card["assigned_to"] is None
    assert card["total"] == 2000
    assert card["items"][0]["description"] == "Alfombra"


async def test_board_excludes_cancelled(auth_client):
    _, _, sale = await _setup(auth_client)
    await auth_client.patch(f"/sales/{sale['id']}", json={"status": "cancelado"})
    assert await _board(auth_client) == []


async def test_board_excludes_delivered(auth_client):
    _, _, sale = await _setup(auth_client)
    await auth_client.patch(f"/sales/{sale['id']}", json={"status": "entregado"})
    assert await _board(auth_client) == []


async def test_board_excludes_delivered_with_work_record(auth_client):
    _, _, sale = await _setup(auth_client)
    await auth_client.patch(f"/work-items/{sale['id']}", json={"status": "en_curso"})
    await auth_client.patch(f"/sales/{sale['id']}", json={"status": "entregado"})
    assert await _board(auth_client) == []


async def test_delivery_auto_closes_existing_card(auth_client, db):
    _, _, sale = await _setup(auth_client)
    await auth_client.patch(f"/work-items/{sale['id']}", json={"status": "en_curso"})
    await auth_client.patch(f"/sales/{sale['id']}", json={"status": "entregado"})
    doc = await db["work_items"].find_one({"sale_id": valid_oid(sale["id"])})
    assert doc is not None
    assert doc["status"] == "terminado"


async def test_delivery_creates_card_terminated(auth_client, db):
    _, _, sale = await _setup(auth_client)
    await auth_client.patch(f"/sales/{sale['id']}", json={"status": "entregado"})
    doc = await db["work_items"].find_one({"sale_id": valid_oid(sale["id"])})
    assert doc is not None
    assert doc["status"] == "terminado"
    assert doc["priority"] == "media"


async def test_reopening_returns_card_to_pending(auth_client, db):
    _, _, sale = await _setup(auth_client)
    users = (await auth_client.get("/users")).json()
    await auth_client.patch(
        f"/work-items/{sale['id']}",
        json={"priority": "alta", "assigned_to": users[0]["id"]},
    )
    await auth_client.post(f"/work-items/{sale['id']}/comments", json={"text": "Nota"})
    await auth_client.patch(f"/sales/{sale['id']}", json={"status": "entregado"})
    await auth_client.patch(f"/sales/{sale['id']}", json={"status": "en_proceso"})
    doc = await db["work_items"].find_one({"sale_id": valid_oid(sale["id"])})
    assert doc is not None
    assert doc["status"] == "pendiente"
    assert doc["priority"] == "alta"
    assert len(doc["comments"]) == 1
    sale_after = (await auth_client.get(f"/sales/{sale['id']}")).json()
    assert sale_after["status"] == "en_proceso"


async def test_non_delivery_status_change_does_not_touch_card(auth_client, db):
    _, _, sale = await _setup(auth_client)
    await auth_client.patch(
        f"/work-items/{sale['id']}", json={"status": "en_curso", "priority": "alta"}
    )
    await auth_client.patch(f"/sales/{sale['id']}", json={"status": "en_proceso"})
    doc = await db["work_items"].find_one({"sale_id": valid_oid(sale["id"])})
    assert doc is not None
    assert doc["status"] == "en_curso"
    assert doc["priority"] == "alta"


async def test_delivered_card_is_frozen(auth_client, db):
    _, _, sale = await _setup(auth_client)
    await auth_client.patch(f"/work-items/{sale['id']}", json={"status": "en_curso"})
    await auth_client.patch(f"/sales/{sale['id']}", json={"status": "entregado"})
    assert (
        await auth_client.patch(f"/work-items/{sale['id']}", json={"status": "bloqueado"})
    ).status_code == 404
    assert (
        await auth_client.post(f"/work-items/{sale['id']}/comments", json={"text": "X"})
    ).status_code == 404
    doc = await db["work_items"].find_one({"sale_id": valid_oid(sale["id"])})
    assert doc["status"] == "terminado"


async def test_terminated_card_does_not_deliver_sale(auth_client):
    _, _, sale = await _setup(auth_client)
    resp = await auth_client.patch(f"/work-items/{sale['id']}", json={"status": "terminado"})
    assert resp.status_code == 200
    sale_after = (await auth_client.get(f"/sales/{sale['id']}")).json()
    assert sale_after["status"] == "pendiente"


async def test_first_change_creates_record_with_defaults(auth_client, db):
    _, _, sale = await _setup(auth_client)
    resp = await auth_client.patch(f"/work-items/{sale['id']}", json={"status": "en_curso"})
    assert resp.status_code == 200
    card = resp.json()
    assert card["status"] == "en_curso"
    assert card["priority"] == "media"
    assert card["assigned_to"] is None
    count = await db["work_items"].count_documents({})
    assert count == 1


async def test_invalid_status_rejected(auth_client):
    _, _, sale = await _setup(auth_client)
    resp = await auth_client.patch(f"/work-items/{sale['id']}", json={"status": "inventado"})
    assert resp.status_code == 422
    card = (await _board(auth_client))[0]
    assert card["status"] == "pendiente"


async def test_invalid_priority_rejected(auth_client):
    _, _, sale = await _setup(auth_client)
    resp = await auth_client.patch(f"/work-items/{sale['id']}", json={"priority": "urgente"})
    assert resp.status_code == 422
    card = (await _board(auth_client))[0]
    assert card["priority"] == "media"


async def test_priority_change(auth_client):
    _, _, sale = await _setup(auth_client)
    resp = await auth_client.patch(f"/work-items/{sale['id']}", json={"priority": "alta"})
    assert resp.status_code == 200
    assert resp.json()["priority"] == "alta"


async def test_assign_active_user(auth_client):
    _, _, sale = await _setup(auth_client)
    users = (await auth_client.get("/users")).json()
    target = users[0]
    resp = await auth_client.patch(f"/work-items/{sale['id']}", json={"assigned_to": target["id"]})
    assert resp.status_code == 200
    assert resp.json()["assigned_to"] == target["id"]

    cleared = await auth_client.patch(f"/work-items/{sale['id']}", json={"assigned_to": None})
    assert cleared.status_code == 200
    assert cleared.json()["assigned_to"] is None


async def test_assign_inactive_user_rejected(auth_client, db):
    _, _, sale = await _setup(auth_client)
    inactive = await users_repo.create_user(
        db,
        {
            "google_sub": "inactive-sub",
            "email": "inactive@x.com",
            "name": "Inactivo",
            "active": False,
            "created_at": utcnow(),
        },
    )
    resp = await auth_client.patch(f"/work-items/{sale['id']}", json={"assigned_to": inactive.id})
    assert resp.status_code == 422


async def test_assign_unknown_user_rejected(auth_client):
    _, _, sale = await _setup(auth_client)
    resp = await auth_client.patch(
        f"/work-items/{sale['id']}", json={"assigned_to": "507f1f77bcf86cd799439011"}
    )
    assert resp.status_code == 422


async def test_add_comment_records_author(auth_client):
    _, _, sale = await _setup(auth_client)
    resp = await auth_client.post(
        f"/work-items/{sale['id']}/comments", json={"text": "  Llamar a la clienta  "}
    )
    assert resp.status_code == 201
    comments = resp.json()["comments"]
    assert len(comments) == 1
    assert comments[0]["text"] == "Llamar a la clienta"
    assert comments[0]["author_name"] == "Test"


async def test_empty_comment_rejected(auth_client):
    _, _, sale = await _setup(auth_client)
    resp = await auth_client.post(f"/work-items/{sale['id']}/comments", json={"text": "   "})
    assert resp.status_code == 422


async def test_filters_combined(auth_client):
    _, _, sale = await _setup(auth_client)
    users = (await auth_client.get("/users")).json()
    target = users[0]
    await auth_client.patch(
        f"/work-items/{sale['id']}",
        json={"priority": "alta", "assigned_to": target["id"]},
    )
    assert len(await _board(auth_client, priority="alta", assigned_to=target["id"])) == 1
    assert await _board(auth_client, priority="baja") == []
    assert await _board(auth_client, assigned_to="507f1f77bcf86cd799439011") == []


async def test_date_order(auth_client):
    _, _, first = await _setup(auth_client)
    other_client = (
        await auth_client.post("/clients", json={"name": "Otra", "type": "minorista"})
    ).json()
    second = (
        await auth_client.post(
            "/sales",
            json={
                "client_id": other_client["id"],
                "date": "2020-01-01T00:00:00Z",
                "items": [{"description": "Libre", "qty": 1, "unit_price": 100}],
            },
        )
    ).json()
    asc = await _board(auth_client, date_sort="asc")
    assert [card["sale_id"] for card in asc] == [second["id"], first["id"]]
    desc = await _board(auth_client, date_sort="desc")
    assert [card["sale_id"] for card in desc] == [first["id"], second["id"]]


async def test_work_change_does_not_touch_sale(auth_client):
    product, _, sale = await _setup(auth_client)
    before = (await auth_client.get(f"/sales/{sale['id']}")).json()
    before_stock = (await auth_client.get(f"/products/{product['id']}")).json()["stock"]

    await auth_client.patch(
        f"/work-items/{sale['id']}", json={"status": "terminado", "priority": "alta"}
    )

    after = (await auth_client.get(f"/sales/{sale['id']}")).json()
    assert after["status"] == before["status"]
    assert after["payments"] == before["payments"]
    assert after["total"] == before["total"]
    after_stock = (await auth_client.get(f"/products/{product['id']}")).json()["stock"]
    assert after_stock == before_stock


async def test_work_requires_auth(client):
    assert (await client.get("/work-items")).status_code == 401
    assert (await client.patch("/work-items/507f1f77bcf86cd799439011", json={})).status_code == 401
