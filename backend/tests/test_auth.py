from app.config import settings
from app.core.security import (
    create_access_token,
    create_oauth_state,
    decode_access_token,
    verify_oauth_state,
)
from app.models import utcnow
from app.repositories import users as users_repo


def test_jwt_roundtrip():
    token = create_access_token("abc", email="a@b.com")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "abc"
    assert payload["email"] == "a@b.com"


def test_invalid_token_returns_none():
    assert decode_access_token("no-es-un-token") is None


def test_oauth_state_roundtrip():
    state = create_oauth_state()
    assert verify_oauth_state(state)
    assert not verify_oauth_state("basura")


async def test_me_requires_token(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_me_with_valid_token(client, db):
    user = await users_repo.create_user(
        db,
        {
            "google_sub": "g1",
            "email": "u@x.com",
            "name": "U",
            "active": True,
            "created_at": utcnow(),
        },
    )
    token = create_access_token(user.id, email=user.email)
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == user.id
    assert response.json()["email"] == "u@x.com"


async def test_me_inactive_user_forbidden(client, db):
    user = await users_repo.create_user(
        db,
        {
            "google_sub": "g2",
            "email": "i@x.com",
            "active": False,
            "created_at": utcnow(),
        },
    )
    token = create_access_token(user.id)
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


async def test_me_token_of_unknown_user(client):
    token = create_access_token("507f1f77bcf86cd799439011")
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


async def test_google_start_returns_authorize_url(client):
    response = await client.get("/auth/google")
    assert response.status_code == 200
    url = response.json()["url"]
    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert "state=" in url
    assert "client_id=" in url


async def test_google_callback_redirects_with_one_time_code(client, db, monkeypatch):
    async def fake_exchange(code: str) -> dict:
        return {
            "sub": "google-123",
            "email": "g@x.com",
            "name": "Gonzalo",
            "picture": "http://img",
        }

    monkeypatch.setattr("app.services.auth.exchange_code_for_userinfo", fake_exchange)
    state = create_oauth_state()
    response = await client.get("/auth/google/callback", params={"code": "abc", "state": state})
    assert response.status_code == 302
    location = response.headers["location"]
    assert "/auth/callback?code=" in location
    auth_code = location.split("code=")[1]

    exchange = await client.post("/auth/exchange", json={"code": auth_code})
    assert exchange.status_code == 200
    data = exchange.json()
    assert data["access_token"]
    assert data["user"]["email"] == "g@x.com"

    again = await client.get(
        "/auth/google/callback", params={"code": "abc", "state": create_oauth_state()}
    )
    assert again.status_code == 302
    second = await client.post(
        "/auth/exchange", json={"code": again.headers["location"].split("code=")[1]}
    )
    assert second.status_code == 200
    assert second.json()["user"]["id"] == data["user"]["id"]


async def test_google_callback_rejects_bad_state(client):
    response = await client.get(
        "/auth/google/callback", params={"code": "abc", "state": "invalido"}
    )
    assert response.status_code == 302
    location = response.headers["location"]
    assert "/login?error=" in location


async def test_google_callback_with_provider_error_redirects_to_login(client):
    response = await client.get("/auth/google/callback", params={"error": "access_denied"})
    assert response.status_code == 302
    assert "/login?error=" in response.headers["location"]


async def test_auth_code_is_single_use(client, db, monkeypatch):
    async def fake_exchange(code: str) -> dict:
        return {"sub": "google-456", "email": "otro@x.com", "name": "Otro"}

    monkeypatch.setattr("app.services.auth.exchange_code_for_userinfo", fake_exchange)
    response = await client.get(
        "/auth/google/callback", params={"code": "abc", "state": create_oauth_state()}
    )
    auth_code = response.headers["location"].split("code=")[1]

    first = await client.post("/auth/exchange", json={"code": auth_code})
    assert first.status_code == 200
    second = await client.post("/auth/exchange", json={"code": auth_code})
    assert second.status_code == 401


async def test_exchange_rejects_unknown_code(client):
    response = await client.post("/auth/exchange", json={"code": "no-existe"})
    assert response.status_code == 401


async def test_local_login_ok(client):
    response = await client.post(
        "/auth/login",
        json={
            "username": settings.local_admin_username,
            "password": settings.local_admin_password,
        },
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_local_login_bad_credentials(client):
    response = await client.post("/auth/login", json={"username": "x", "password": "y"})
    assert response.status_code == 401
