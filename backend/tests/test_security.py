from app.config import settings
from app.middleware import reset_rate_limits


async def test_security_headers_present(client):
    response = await client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in response.headers
    assert "Strict-Transport-Security" not in response.headers


async def test_hsts_header_in_production(client):
    original = settings.env
    settings.env = "production"
    try:
        response = await client.get("/health")
    finally:
        settings.env = original
    assert "Strict-Transport-Security" in response.headers


async def test_health_reports_services(client):
    original = settings.ollama_base_url
    settings.ollama_base_url = "http://127.0.0.1:1"
    try:
        response = await client.get("/health")
    finally:
        settings.ollama_base_url = original
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert set(body["services"]) == {"mongo", "ollama"}


async def test_rate_limit_returns_429_with_retry_after(client):
    settings.rate_limit_enabled = True
    settings.rate_limit_global = 2
    reset_rate_limits()
    try:
        responses = [await client.get("/providers") for _ in range(3)]
    finally:
        settings.rate_limit_enabled = False
    assert [r.status_code for r in responses] == [401, 401, 429]
    limited = responses[2]
    assert limited.headers["Retry-After"].isdigit()
    assert limited.headers["X-Content-Type-Options"] == "nosniff"


async def test_health_is_exempt_from_rate_limit(client):
    original = settings.ollama_base_url
    settings.rate_limit_enabled = True
    settings.rate_limit_global = 1
    settings.ollama_base_url = "http://127.0.0.1:1"
    reset_rate_limits()
    try:
        responses = [await client.get("/health") for _ in range(3)]
    finally:
        settings.rate_limit_enabled = False
        settings.rate_limit_global = 120
        settings.ollama_base_url = original
    assert [r.status_code for r in responses] == [200, 200, 200]


async def test_chat_stream_shares_chat_window_and_keeps_write_window(client):
    settings.rate_limit_enabled = True
    settings.rate_limit_chat = 1
    settings.rate_limit_write = 4
    reset_rate_limits()
    payload = {"thread_id": "hilo-rl", "message": "hola"}
    try:
        stream = [
            await client.post("/chat/stream", json=payload),
            await client.post("/chat/stream", json=payload),
        ]
        confirm = await client.post("/chat/confirm", json={"thread_id": "hilo-rl", "token": "x"})
        threads = [
            await client.post("/chat/threads", json={"thread_id": "hilo-rl"}),
            await client.post("/chat/threads", json={"thread_id": "hilo-rl"}),
            await client.post("/chat/threads", json={"thread_id": "hilo-rl-2"}),
            await client.post("/chat/threads", json={"thread_id": "hilo-rl-3"}),
        ]
    finally:
        settings.rate_limit_enabled = False
        settings.rate_limit_chat = 20
        settings.rate_limit_write = 60
    assert [r.status_code for r in stream] == [401, 429]
    assert stream[1].headers["Retry-After"].isdigit()
    assert confirm.status_code == 401
    assert [r.status_code for r in threads] == [401, 401, 401, 429]


async def test_oversized_body_is_rejected(client):
    payload = "x" * 2_100_000
    response = await client.post(
        "/auth/login",
        content=payload,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert "demasiado grande" in response.json()["detail"]


async def test_local_login_disabled_returns_401(client):
    settings.enable_local_login = False
    try:
        response = await client.post(
            "/auth/login", json={"username": "admin", "password": "cambiar-esta-clave"}
        )
    finally:
        settings.enable_local_login = True
    assert response.status_code == 401


async def test_local_login_blocked_in_production(client):
    original_env = settings.env
    settings.env = "production"
    try:
        response = await client.post(
            "/auth/login", json={"username": "admin", "password": "cambiar-esta-clave"}
        )
    finally:
        settings.env = original_env
    assert response.status_code == 401
