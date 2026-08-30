"""
Automated unit tests for empirical precision sweep and evaluation matrix in eval_suite.py.
"""

# pyrefly: ignore [missing-import]
import pytest
from eval_suite import EVALUATION_SEED_DATA, run_precision_sweep


def test_evaluation_seed_matrix_structure():
    """Verify evaluation dataset matrix contains valid ground truth cases."""
    assert len(EVALUATION_SEED_DATA) == 15
    for case in EVALUATION_SEED_DATA:
        assert "post_id" in case
        assert "post" in case
        assert "image_desc" in case
        assert "category_post" in case
        assert "category_img" in case
        assert "expected" in case
        assert isinstance(case["expected"], bool)


def test_run_precision_sweep_execution():
    """Verify precision sweep executes successfully and achieves optimal accuracy."""
    best_threshold, best_accuracy = run_precision_sweep()
    assert 0.40 <= best_threshold <= 0.65
    assert best_accuracy >= 90.0
