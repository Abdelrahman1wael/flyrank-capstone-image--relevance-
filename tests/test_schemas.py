"""
Unit tests for boundary schemas and data models in engine.schemas.
"""

# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from engine.schemas import (
    VisionProfileSchema,
    ImageMetadataResponse,
    MatchRequest,
    MatchCandidate,
    MatchResponse,
    ReviewActionRequest,
    ReviewLedgerEntry
)


def test_vision_profile_schema_valid():
    """Verify high-confidence vision profile schema instantiation."""
    profile = VisionProfileSchema(
        image_id="fox_01",
        file_path="assets/fox.jpg",
        subject="Red Fox",
        category="fox",
        attributes=["auburn fur", "bushy tail"],
        caption="A beautiful red fox trotting through autumn foliage",
        confidence=0.92
    )
    assert profile.image_id == "fox_01"
    assert profile.confidence == 0.92
    assert "auburn fur" in profile.attributes


def test_vision_profile_schema_exact_boundary():
    """Verify exact 0.75 confidence score passes boundary constraint."""
    profile = VisionProfileSchema(
        image_id="fox_boundary",
        file_path="assets/fox_boundary.jpg",
        subject="Red Fox",
        category="fox",
        attributes=["red coat"],
        caption="A clear photograph of a red fox",
        confidence=0.75
    )
    assert profile.confidence == 0.75


def test_vision_profile_schema_low_confidence_rejection():
    """Verify confidence below 0.75 floor raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        VisionProfileSchema(
            image_id="blurry_01",
            file_path="assets/blurry.jpg",
            subject="unclear animal",
            category="unknown",
            attributes=["shadow"],
            caption="Inconclusive visual analysis of blurry shape",
            confidence=0.74
        )
    assert "0.75 confidence floor" in str(exc_info.value)


def test_vision_profile_schema_min_length_validations():
    """Verify minimum length validations for subject, category, and caption."""
    # Subject too short (< 2 chars)
    with pytest.raises(ValidationError):
        VisionProfileSchema(
            image_id="test_01",
            file_path="assets/test.jpg",
            subject="x",
            category="fox",
            caption="Valid descriptive caption text",
            confidence=0.85
        )

    # Caption too short (< 10 chars)
    with pytest.raises(ValidationError):
        VisionProfileSchema(
            image_id="test_01",
            file_path="assets/test.jpg",
            subject="Red Fox",
            category="fox",
            caption="Short",
            confidence=0.85
        )


def test_image_metadata_response_defaults():
    """Verify ImageMetadataResponse initialization and default metrics."""
    meta = ImageMetadataResponse(
        image_id="img_100",
        file_path="assets/img.jpg",
        subject="Wolf",
        category="wolf",
        attributes=["grizzled coat"],
        caption="An imposing grey wolf standing on a rocky ridge",
        confidence=0.98
    )
    assert meta.tokens_consumed == 0
    assert meta.cost_usd == 0.0


def test_match_request_validation():
    """Verify MatchRequest validation rules."""
    req = MatchRequest(post_id="p_10", post_text="Valid article title or content")
    assert req.post_id == "p_10"

    # Invalid post_text (< 5 chars)
    with pytest.raises(ValidationError):
        MatchRequest(post_id="p_10", post_text="Tiny")


def test_review_action_request_normalization():
    """Verify ReviewActionRequest upper-cases action input and rejects invalid actions."""
    req1 = ReviewActionRequest(post_id="p_01", image_id="fox_01", action="approved")
    assert req1.action == "APPROVED"

    req2 = ReviewActionRequest(post_id="p_01", image_id="fox_01", action="REJECTED")
    assert req2.action == "REJECTED"

    with pytest.raises(ValidationError) as exc_info:
        ReviewActionRequest(post_id="p_01", image_id="fox_01", action="INVALID_ACTION")
    assert "Action must be either 'APPROVED' or 'REJECTED'" in str(exc_info.value)
