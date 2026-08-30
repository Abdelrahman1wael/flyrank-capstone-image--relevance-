"""
Automated Pytest Test Suite for FlyRank AI Image Understanding Engine.
"""

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from engine.schemas import VisionProfileSchema, ReviewActionRequest
from engine.services import MatchingService
from engine.database import init_db, save_image_record, save_image_embedding
from engine.main import app

client = TestClient(app)


def setup_module(module):
    """Setup in-memory/sqlite database before running tests."""
    init_db()
    
    # Save a mock red fox asset
    save_image_record(
        image_id="test_fox_01",
        file_path="assets/fox.jpg",
        subject="Red Fox",
        category="fox",
        attributes=["auburn fur", "pointed snout"],
        caption="A vibrant red fox in autumn leaves",
        confidence=0.95,
        tokens_consumed=1250,
        cost_usd=0.0001
    )
    # Save a mock grey wolf asset
    save_image_record(
        image_id="test_wolf_01",
        file_path="assets/wolf.jpg",
        subject="Grey Wolf",
        category="wolf",
        attributes=["grizzled fur", "pack predator"],
        caption="An imposing grey wolf standing on a rocky ridge",
        confidence=0.97,
        tokens_consumed=1250,
        cost_usd=0.0001
    )

    # Encode embeddings using matching service
    service = MatchingService()
    emb_fox = service.embed_model.encode("A vibrant red fox in autumn leaves focusing on Red Fox (fox)").tolist()
    emb_wolf = service.embed_model.encode("An imposing grey wolf standing on a rocky ridge focusing on Grey Wolf (wolf)").tolist()

    save_image_embedding("test_fox_01", emb_fox)
    save_image_embedding("test_wolf_01", emb_wolf)


def test_low_confidence_pydantic_floor_exception():
    """Boundary schema rejects insecure scores under 0.75 floor."""
    with pytest.raises(ValidationError) as exc_info:
        VisionProfileSchema(
            image_id="blurry_99",
            file_path="assets/blurry.jpg",
            subject="blurry shadow",
            category="unknown",
            attributes=["dark"],
            caption="Inconclusive camera capture text",
            confidence=0.42
        )
    assert "0.75 confidence floor" in str(exc_info.value)


def test_mismatch_guard_blocks_wolf_trap():
    """Direct Fox-Post to Wolf-Asset Refusal scenario."""
    service = MatchingService(threshold=0.54)
    post_content = "The biological feeding preferences and behavior of wild red foxes."
    
    response = service.evaluate_candidates(post_id="test_p1", post_text=post_content)
    
    # Verify wolf candidate was rejected by guard
    wolf_candidates = [c for c in response.all_candidates if c.image_id == "test_wolf_01"]
    assert len(wolf_candidates) > 0
    wolf_cand = wolf_candidates[0]
    assert wolf_cand.guard_status == "REJECTED_BY_GUARD"
    assert "Concept crossover failure" in wolf_cand.explanation


def test_confident_match_absence_behavior():
    """Out of domain query cleanly returns match_found = False."""
    service = MatchingService(threshold=0.54)
    out_of_domain_post = "Deep sea oil rig drilling and underwater pipeline maintenance."
    
    response = service.evaluate_candidates(post_id="test_p2", post_text=out_of_domain_post)
    assert response.match_found is False
    assert response.recommendation is None
    assert "No confident match available" in response.system_resolution


def test_fastapi_health_endpoint():
    """Verify GET /health returns 200 HEALTHY."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "HEALTHY"


def test_fastapi_get_post_images_endpoint():
    """Verify GET /posts/{id}/images endpoint."""
    res = client.get("/posts/p_01/images")
    assert res.status_code == 200
    data = res.json()
    assert "post_id" in data
    assert "system_resolution" in data


def test_fastapi_review_action_endpoint():
    """Verify POST /review/action endpoint."""
    payload = {
        "post_id": "test_p1",
        "image_id": "test_fox_01",
        "action": "APPROVED"
    }
    res = client.post("/review/action", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"


def test_fastapi_review_ledger_endpoint():
    """Verify GET /review/ledger endpoint."""
    res = client.get("/review/ledger")
    assert res.status_code == 200
    data = res.json()
    assert "review_ledger" in data
    assert "cost_telemetry" in data
