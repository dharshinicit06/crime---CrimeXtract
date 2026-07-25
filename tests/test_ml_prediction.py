"""Tests for the ML prediction API endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        yield ac


class TestMLPrediction:
    """Integration tests for POST /api/v1/ml/predict."""

    async def test_predict_success(self, client):
        """Should return 200 with predicted_cases for valid input."""
        payload = {
            "state": "Karnataka",
            "district": "Bengaluru Urban",
            "year": 2025,
            "crime_type": "Murder",
            "chargesheeted": 50,
            "convictions": 20,
            "population": 8500000,
        }
        resp = await client.post("/api/v1/ml/predict", json=payload)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "predicted_cases" in data
        assert isinstance(data["predicted_cases"], float | int)
        assert data["predicted_cases"] >= 0

    async def test_predict_unknown_state(self, client):
        """Should return 400 for an unknown state."""
        payload = {
            "state": "NonExistentState",
            "district": "Bengaluru Urban",
            "year": 2025,
            "crime_type": "Murder",
            "chargesheeted": 10,
            "convictions": 2,
            "population": 100000,
        }
        resp = await client.post("/api/v1/ml/predict", json=payload)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"

    async def test_predict_unknown_district(self, client):
        """Should return 400 for an unknown district."""
        payload = {
            "state": "Karnataka",
            "district": "FakeDistrict",
            "year": 2025,
            "crime_type": "Murder",
            "chargesheeted": 10,
            "convictions": 2,
            "population": 100000,
        }
        resp = await client.post("/api/v1/ml/predict", json=payload)
        assert resp.status_code == 400

    async def test_predict_unknown_crime_type(self, client):
        """Should return 400 for an unknown crime type."""
        payload = {
            "state": "Karnataka",
            "district": "Bengaluru Urban",
            "year": 2025,
            "crime_type": "FakeCrime",
            "chargesheeted": 10,
            "convictions": 2,
            "population": 100000,
        }
        resp = await client.post("/api/v1/ml/predict", json=payload)
        assert resp.status_code == 400

    async def test_predict_validation_error(self, client):
        """Should return 422 for invalid field values."""
        payload = {
            "state": "Karnataka",
            "district": "Bengaluru Urban",
            "year": "invalid",
            "crime_type": "Murder",
            "chargesheeted": 10,
            "convictions": 2,
            "population": 100000,
        }
        resp = await client.post("/api/v1/ml/predict", json=payload)
        assert resp.status_code == 422

    async def test_predict_convictions_exceed_chargesheeted(self, client):
        """Should return 422 when convictions > chargesheeted."""
        payload = {
            "state": "Karnataka",
            "district": "Bengaluru Urban",
            "year": 2025,
            "crime_type": "Murder",
            "chargesheeted": 5,
            "convictions": 10,
            "population": 100000,
        }
        resp = await client.post("/api/v1/ml/predict", json=payload)
        assert resp.status_code == 422
