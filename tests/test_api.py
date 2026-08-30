"""
Integration and API boundary tests for FastAPI router endpoints in engine.main.
"""

# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient

from engine.database import init_db, save_image_record, save_image_embedding
from engine.main import app, SAMPLE_POSTS

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_api_test_environment(tmp_path, monkeypatch):
    """Initializes isolated database and populates sample assets for API testing."""
    test_db_file = str(tmp_path / "test_api_flyrank.db")
    monkeypatch.setattr("engine.database.DB_FILE", test_db_file)
    init_db()

    # Seed mock image record
    save_image_record(
        image_id="fox_api_01",
        file_path="assets/fox_api.jpg",
        subject="Red Fox",
        category="fox",
        attributes=["red coat"],
        caption="A vibrant red fox in autumn leaves",
        confidence=0.95,
        tokens_consumed=1000,
        cost_usd=0.0001
    )
    # Mock vector matching service embedding length
    dummy_vec = [0.1] * 384
    save_image_embedding("fox_api_01", dummy_vec)


def test_health_check_endpoint():
    """Verify GET /health returns 200 HEALTHY."""
    res = client.get("/health")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["status"] == "HEALTHY"
    assert "FlyRank" in json_data["engine"]


def test_get_images_for_sample_post():
    """Verify GET /posts/{id}/images works with sample catalog post ID."""
    res = client.get("/posts/p_01/images")
    assert res.status_code == 200
    data = res.json()
    assert data["post_id"] == "p_01"
    assert "system_resolution" in data
    assert "all_candidates" in data


def test_get_images_with_custom_query_override():
    """Verify GET /posts/{id}/images supports custom query override."""
    res = client.get("/posts/p_99/images?query=Custom+red+fox+article+text")
    assert res.status_code == 200
    data = res.json()
    assert data["post_id"] == "p_99"


def test_review_action_endpoint_success():
    """Verify POST /review/action succeeds for APPROVED action."""
    payload = {
        "post_id": "p_01",
        "image_id": "fox_api_01",
        "action": "APPROVED"
    }
    res = client.post("/review/action", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"


def test_review_action_endpoint_case_insensitivity():
    """Verify POST /review/action handles lowercase 'rejected' payload."""
    payload = {
        "post_id": "p_01",
        "image_id": "fox_api_01",
        "action": "rejected"
    }
    res = client.post("/review/action", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"


def test_review_action_endpoint_validation_error():
    """Verify POST /review/action returns 422 for invalid action string."""
    payload = {
        "post_id": "p_01",
        "image_id": "fox_api_01",
        "action": "INVALID_ACTION"
    }
    res = client.post("/review/action", json=payload)
    assert res.status_code == 422


def test_review_ledger_endpoint():
    """Verify GET /review/ledger exposes review entries and telemetry logs."""
    res = client.get("/review/ledger")
    assert res.status_code == 200
    data = res.json()
    assert "review_ledger" in data
    assert "cost_telemetry" in data
    assert isinstance(data["review_ledger"], list)
    assert isinstance(data["cost_telemetry"], list)
