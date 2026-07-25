"""Tests for the chatbot intent routing and tool integration."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# Import the classification function for isolated testing
from app.chat.services import _classify_intent as classify

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        yield ac


async def _get_auth_token() -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        resp = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@ksp.gov.in", "password": "admin123"},
        )
        if resp.status_code == 200:
            return resp.json()["access_token"]
        return ""


class TestIntentRouting:
    """Test that intent classification works correctly (sync tests)."""

    def test_fir_intent(self):
        assert classify("Show me FIR 123") is not None
        assert classify("Show me FIR 123")[0] == "fir_search"

    def test_fir_with_number(self):
        assert classify("Find case FIR-2026-00001") is not None
        assert classify("Find case FIR-2026-00001")[0] == "fir_search"

    def test_analytics_summary_intent(self):
        assert classify("What is the overall crime summary?") is not None
        assert classify("What is the overall crime summary?")[0] == "analytics_summary"

    def test_hotspots_intent(self):
        assert classify("Show crime hotspots in Bengaluru") is not None
        assert classify("Show crime hotspots in Bengaluru")[0] == "hotspots"

    def test_crime_by_type_intent(self):
        assert classify("Show me crime by type") is not None
        assert classify("Show me crime by type")[0] == "crime_by_type"

    def test_solved_vs_pending_intent(self):
        assert classify("How many solved cases?") is not None
        assert classify("How many solved cases?")[0] == "solved_vs_pending"

    def test_network_intent(self):
        assert classify("Show criminal network connections") is not None
        assert classify("Show criminal network connections")[0] == "network"

    def test_offender_intent(self):
        assert classify("Get offender profile for accused 42") is not None
        assert classify("Get offender profile for accused 42")[0] == "offender_profile"

    def test_prediction_intent(self):
        assert classify("Predict murder cases for next year") is not None
        assert classify("Predict murder cases for next year")[0] == "prediction"

    def test_general_query_no_intent(self):
        assert classify("Hello, how are you today?") is None

    def test_unknown_query_no_intent(self):
        assert classify("What is the capital of France?") is None


class TestChatAuth:
    """Still enforce authentication."""

    async def test_missing_jwt_returns_401(self, client):
        resp = await client.post("/api/v1/chat/message", json={"message": "Hello"})
        assert resp.status_code == 401


class TestChatToolsIntegration:
    """Integration tests for the chat endpoint — require running database."""

    async def test_chat_endpoint_works_with_jwt(self, client):
        token = await _get_auth_token()
        if not token:
            pytest.skip("No auth token - test user may not exist in DB")

        resp = await client.post(
            "/api/v1/chat/message",
            json={"message": "Hello CrimeAI"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "conversation_id" in data
        assert data["status"] == "success"

    async def test_fir_query_via_chat(self, client):
        token = await _get_auth_token()
        if not token:
            pytest.skip("No auth token")

        resp = await client.post(
            "/api/v1/chat/message",
            json={"message": "Show FIR 123"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["response"]) > 0

    async def test_hotspots_query_via_chat(self, client):
        token = await _get_auth_token()
        if not token:
            pytest.skip("No auth token")

        resp = await client.post(
            "/api/v1/chat/message",
            json={"message": "Show crime hotspots"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["response"]) > 0

    async def test_analytics_query_via_chat(self, client):
        token = await _get_auth_token()
        if not token:
            pytest.skip("No auth token")

        resp = await client.post(
            "/api/v1/chat/message",
            json={"message": "Show crime statistics summary"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["response"]) > 0

    async def test_empty_message_still_fails(self, client):
        token = await _get_auth_token()
        if not token:
            pytest.skip("No auth token")

        resp = await client.post(
            "/api/v1/chat/message",
            json={"message": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
