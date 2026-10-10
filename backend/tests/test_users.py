from app.models import utcnow
from app.repositories import users as users_repo


async def test_lists_only_active_users(auth_client, db):
    await users_repo.create_user(
        db,
        {
            "google_sub": "inactive-sub",
            "email": "inactive@x.com",
            "name": "Inactivo",
            "active": False,
            "created_at": utcnow(),
        },
    )
    resp = await auth_client.get("/users")
    assert resp.status_code == 200
    emails = [user["email"] for user in resp.json()]
    assert "test@x.com" in emails
    assert "inactive@x.com" not in emails
    assert resp.json()[0]["id"]


async def test_users_require_auth(client):
    assert (await client.get("/users")).status_code == 401
