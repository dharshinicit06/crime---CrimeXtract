"""Integration tests for health monitoring endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_database_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        r = await client.get("/health/database")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "latency_ms" in data


@pytest.mark.asyncio
async def test_health_ml_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        r = await client.get("/health/ml")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_health_gemini_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        r = await client.get("/health/gemini")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_version_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        r = await client.get("/version")
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
