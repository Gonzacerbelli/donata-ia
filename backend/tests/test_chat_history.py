async def test_chat_thread_lifecycle(auth_client):
    created = await auth_client.post(
        "/chat/threads", json={"thread_id": "hilo-1", "title": "Consulta"}
    )
    assert created.status_code == 201
    assert created.json()["thread_id"] == "hilo-1"

    listed = await auth_client.get("/chat/threads")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    renamed = await auth_client.patch("/chat/threads/hilo-1", json={"title": "Nuevo"})
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Nuevo"

    messages = await auth_client.get("/chat/threads/hilo-1/messages")
    assert messages.status_code == 200
    assert messages.json() == []

    deleted = await auth_client.delete("/chat/threads/hilo-1")
    assert deleted.status_code == 204
    assert (await auth_client.get("/chat/threads")).json() == []


async def test_chat_create_thread_is_idempotent(auth_client):
    first = await auth_client.post("/chat/threads", json={"thread_id": "hilo-x"})
    second = await auth_client.post("/chat/threads", json={"thread_id": "hilo-x"})
    assert first.json()["id"] == second.json()["id"]


async def test_chat_threads_are_scoped_to_user(auth_client, client, db):
    from app.core.security import create_access_token
    from app.models import utcnow
    from app.repositories import users as users_repo

    await auth_client.post("/chat/threads", json={"thread_id": "privado"})

    other = await users_repo.create_user(
        db,
        {
            "google_sub": "other",
            "email": "other@x.com",
            "active": True,
            "created_at": utcnow(),
        },
    )
    token = create_access_token(other.id, email=other.email)
    response = await client.get(
        "/chat/threads/privado/messages", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
    others = await client.get("/chat/threads", headers={"Authorization": f"Bearer {token}"})
    assert others.json() == []


async def test_chat_routes_require_auth(client):
    assert (await client.get("/chat/threads")).status_code == 401
