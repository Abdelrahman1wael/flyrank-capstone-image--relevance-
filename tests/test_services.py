"""
Unit tests for core vector matching engine and Mismatch Guard in engine.services.
"""

# pyrefly: ignore [missing-import]
import pytest
import numpy as np
from unittest.mock import patch

from engine.services import calculate_cosine_similarity, MatchingService
from engine.schemas import MatchCandidate, MatchResponse


def test_calculate_cosine_similarity_identical_vectors():
    """Identical non-zero vectors must return 1.0 cosine similarity."""
    vec_a = [1.0, 2.0, 3.0]
    vec_b = [1.0, 2.0, 3.0]
    sim = calculate_cosine_similarity(vec_a, vec_b)
    assert pytest.approx(sim, 1e-5) == 1.0


def test_calculate_cosine_similarity_orthogonal_vectors():
    """Orthogonal vectors must return 0.0 cosine similarity."""
    vec_a = [1.0, 0.0]
    vec_b = [0.0, 1.0]
    sim = calculate_cosine_similarity(vec_a, vec_b)
    assert pytest.approx(sim, 1e-5) == 0.0


def test_calculate_cosine_similarity_opposite_vectors():
    """Opposite vectors must return -1.0 cosine similarity."""
    vec_a = [1.0, 2.0]
    vec_b = [-1.0, -2.0]
    sim = calculate_cosine_similarity(vec_a, vec_b)
    assert pytest.approx(sim, 1e-5) == -1.0


def test_calculate_cosine_similarity_zero_vectors():
    """Zero-magnitude vectors must return 0.0 safely without division by zero errors."""
    assert calculate_cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0
    assert calculate_cosine_similarity([1.0, 2.0], [0.0, 0.0]) == 0.0
    assert calculate_cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0


def test_check_taxonomic_mismatch_fox_vs_wolf():
    """Mismatch Guard correctly identifies Fox post vs Wolf asset crossover."""
    service = MatchingService(threshold=0.54)

    # Fox post vs Wolf asset
    is_mismatch, explanation = service.check_taxonomic_mismatch(
        post_text="Behavioral habits of wild red foxes",
        candidate_subject="Grey Wolf",
        candidate_category="wolf"
    )
    assert is_mismatch is True
    assert "fox" in explanation.lower() and "wolf" in explanation.lower()


def test_check_taxonomic_mismatch_wolf_vs_fox():
    """Mismatch Guard correctly identifies Wolf post vs Fox asset crossover."""
    service = MatchingService(threshold=0.54)

    is_mismatch, explanation = service.check_taxonomic_mismatch(
        post_text="Pack dynamics of wild wolves in Wyoming",
        candidate_subject="Red Fox",
        candidate_category="fox"
    )
    assert is_mismatch is True
    assert "wolf" in explanation.lower() and "fox" in explanation.lower()


def test_check_taxonomic_mismatch_herbivore_vs_bear():
    """Mismatch Guard correctly identifies Herbivore/Deer post vs Bear asset crossover."""
    service = MatchingService(threshold=0.54)

    is_mismatch, explanation = service.check_taxonomic_mismatch(
        post_text="Woodland foraging patterns of whitetail deer and cervid species",
        candidate_subject="Grizzly Bear",
        candidate_category="bear"
    )
    assert is_mismatch is True
    assert "herbivore" in explanation.lower() or "bear" in explanation.lower()


def test_check_taxonomic_mismatch_valid_pairing():
    """Valid conceptual pair returns mismatch=False."""
    service = MatchingService(threshold=0.54)

    is_mismatch, explanation = service.check_taxonomic_mismatch(
        post_text="Territorial marking of red foxes",
        candidate_subject="Red Fox",
        candidate_category="fox"
    )
    assert is_mismatch is False
    assert explanation == ""


@patch("engine.services.get_all_images_with_embeddings")
def test_evaluate_candidates_empty_datastore(mock_get_all):
    """Evaluating when database has no images returns match_found=False cleanly."""
    mock_get_all.return_value = []
    service = MatchingService(threshold=0.54)

    res = service.evaluate_candidates("p_test", "Red fox hunting habits")
    assert res.match_found is False
    assert res.recommendation is None
    assert res.all_candidates == []
    assert "No indexed images" in res.system_resolution


@patch("engine.services.log_review_action")
@patch("engine.services.get_all_images_with_embeddings")
def test_evaluate_candidates_ranking_and_threshold_gate(mock_get_all, mock_log):
    """Verify evaluation ranks candidates descending by similarity and applies threshold gate."""
    # Mock candidate vectors
    service = MatchingService(threshold=0.50)
    mock_vec_post = service.embed_model.encode("Red fox hunting habits").tolist()

    mock_get_all.return_value = [
        {
            "image_id": "img_fox_high",
            "file_path": "assets/fox_high.jpg",
            "subject": "Red Fox",
            "category": "fox",
            "caption": "Red fox hunting in autumn grass",
            "confidence": 0.95,
            "embedding": mock_vec_post
        },
        {
            "image_id": "img_fox_low",
            "file_path": "assets/fox_low.jpg",
            "subject": "Red Fox",
            "category": "fox",
            "caption": "Unrelated topic caption",
            "confidence": 0.80,
            "embedding": [0.0] * len(mock_vec_post)
        }
    ]

    res = service.evaluate_candidates("p_rank", "Red fox hunting habits")
    assert res.match_found is True
    assert res.recommendation is not None
    assert res.recommendation.image_id == "img_fox_high"
    assert res.recommendation.similarity_score > 0.50
    assert len(res.all_candidates) == 2
    # Verify descending sort order
    assert res.all_candidates[0].similarity_score >= res.all_candidates[1].similarity_score
