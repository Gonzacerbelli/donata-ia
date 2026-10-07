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
        settings.ollama_base_url = original
    assert [r.status_code for r in responses] == [200, 200, 200]
