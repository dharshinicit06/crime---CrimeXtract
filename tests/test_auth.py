"""Integration tests for authentication endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Verify the health endpoint returns basic status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_version_endpoint():
    """Verify the version endpoint returns app version."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        r = await client.get("/version")
    assert r.status_code == 200
    assert "message" in r.json()


@pytest.mark.asyncio
async def test_login_missing_fields():
    """Test that missing login fields return validation error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        r = await client.post("/auth/login", json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Test that invalid credentials return 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        r = await client.post("/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_no_token():
    """Test that protected endpoints return 401 without JWT."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        r = await client.get("/chat/conversations")
    assert r.status_code == 401
