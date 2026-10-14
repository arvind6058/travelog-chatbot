import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import get_settings

settings = get_settings()


@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == settings.PROJECT_NAME
        assert data["status"] == "operational"


@pytest.mark.asyncio
async def test_basic_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app"] == settings.PROJECT_NAME
        assert data["version"] == settings.VERSION
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_api_v1_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_db_health_check_returns_valid_structure():
    """Ensure db health check never lies: returns status connected or disconnected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/db")
        # May be 200 if connected or 503 if disconnected, but MUST have structured response
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert data["status"] in ["connected", "disconnected"]


@pytest.mark.asyncio
async def test_redis_health_check_returns_valid_structure():
    """Ensure redis health check never lies: returns status connected or disconnected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/redis")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert data["status"] in ["connected", "disconnected"]


@pytest.mark.asyncio
async def test_readiness_probe_structure():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/ready")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "ready" in data
        assert "database" in data
        assert "redis" in data


@pytest.mark.asyncio
async def test_cors_headers():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        origin = settings.cors_origins_list[0]
        headers = {
            "Origin": origin,
            "Access-Control-Request-Method": "GET"
        }
        response = await client.options("/health", headers=headers)
        assert response.headers.get("access-control-allow-origin") == origin


@pytest.mark.asyncio
async def test_not_found_error_structure():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/non_existent_route_404")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "HTTP_404"
