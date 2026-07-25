"""Tests for the Chat API endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        yield ac


async def _get_auth_token() -> str:
    """Obtain a valid JWT by logging in.

    This depends on the test user existing in the database.
    If the user does not exist, the login will fail and tests
    that require auth will need to be adjusted.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        resp = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@ksp.gov.in", "password": "admin123"},
        )
        if resp.status_code == 200:
            return resp.json()["access_token"]
        return ""


class TestChatUnauthenticated:
    """Tests for requests without a JWT token."""

    async def test_missing_jwt_returns_401(self, client):
        """POST /api/v1/chat/message without JWT should return 401."""
        payload = {"message": "Hello"}
        resp = await client.post("/api/v1/chat/message", json=payload)
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    async def test_invalid_jwt_returns_401(self, client):
        """POST /api/v1/chat/message with invalid JWT should return 401."""
        payload = {"message": "Hello"}
        resp = await client.post(
            "/api/v1/chat/message",
            json=payload,
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        assert resp.status_code == 401


class TestChatValidation:
    """Tests for request validation."""

    async def test_empty_message_returns_422(self, client):
        """Empty message should trigger Pydantic validation error (422)."""
        payload = {"message": ""}
        resp = await client.post(
            "/api/v1/chat/message",
            json=payload,
            headers={"Authorization": "Bearer test"},
        )
        # Pydantic validates min_length first
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    async def test_message_exceeds_max_length_returns_422(self, client):
        """Message over 2000 chars should trigger validation error."""
        payload = {"message": "x" * 2001}
        resp = await client.post(
            "/api/v1/chat/message",
            json=payload,
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 422


class TestChatAuthenticated:
    """Tests for authenticated requests to the chat endpoint."""

    async def test_send_message_returns_200(self, client):
        """Authenticated request should return 200 with ChatResponse."""
        token = await _get_auth_token()
        if not token:
            pytest.skip("No auth token - test user may not exist in DB")

        payload = {"message": "Show me burglary cases in Bengaluru"}
        resp = await client.post(
            "/api/v1/chat/message",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

        data = resp.json()
        assert "response" in data
        assert "conversation_id" in data
        assert "timestamp" in data
        assert "status" in data

        assert data["status"] == "success"
        assert len(data["conversation_id"]) > 0
        assert len(data["response"]) > 0

    async def test_conversation_id_is_auto_generated(self, client):
        """When conversation_id is omitted, one should be generated."""
        token = await _get_auth_token()
        if not token:
            pytest.skip("No auth token")

        payload = {"message": "Show solved cases"}
        resp = await client.post(
            "/api/v1/chat/message",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["conversation_id"] is not None
        assert len(data["conversation_id"]) >= 16

    async def test_send_message_returns_valid_structure(self, client):
        """Authenticated request should return the expected response shape."""
        token = await _get_auth_token()
        if not token:
            pytest.skip("No auth token")

        test_message = "Show top crime hotspots"
        payload = {"message": test_message}
        resp = await client.post(
            "/api/v1/chat/message",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert len(data["response"]) > 0
        assert "conversation_id" in data
        assert data["status"] == "success"

    async def test_send_message_with_existing_conversation(self, client):
        """Conversation ID should persist when provided."""
        token = await _get_auth_token()
        if not token:
            pytest.skip("No auth token")

        conv_id = "test-conversation-abc-123"
        payload = {"message": "Analyze crime patterns", "conversation_id": conv_id}
        resp = await client.post(
            "/api/v1/chat/message",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["conversation_id"] == conv_id
