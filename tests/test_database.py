"""
Unit tests for database infrastructure and SQLite CRUD operations in engine.database.
"""

import os
# pyrefly: ignore [missing-import]
import pytest
import sqlite3
from unittest.mock import patch

from engine.database import (
    init_db,
    save_image_record,
    save_image_embedding,
    get_all_images_with_embeddings,
    log_review_action,
    update_review_status,
    fetch_review_ledger,
    fetch_cost_telemetry
)


@pytest.fixture(autouse=True)
def setup_fresh_test_db(tmp_path, monkeypatch):
    """Fixture ensuring each test runs in an isolated SQLite database file."""
    test_db_file = str(tmp_path / "test_flyrank.db")
    monkeypatch.setattr("engine.database.DB_FILE", test_db_file)
    init_db()
    return test_db_file


def test_init_db_creates_tables(setup_fresh_test_db):
    """Verify init_db initializes expected schema tables."""
    conn = sqlite3.connect(setup_fresh_test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert "images" in tables
    assert "image_embeddings" in tables
    assert "posts" in tables
    assert "review_ledger" in tables


def test_save_and_retrieve_image_with_embedding():
    """Verify inserting image metadata and embeddings, then fetching joined records."""
    save_image_record(
        image_id="img_fox_01",
        file_path="assets/fox_01.jpg",
        subject="Red Fox",
        category="fox",
        attributes=["red coat", "white chest"],
        caption="A vibrant red fox in autumn leaves",
        confidence=0.96,
        tokens_consumed=1250,
        cost_usd=0.00015
    )

    vector = [0.1, 0.2, 0.3, 0.4]
    save_image_embedding("img_fox_01", vector)

    records = get_all_images_with_embeddings()
    assert len(records) == 1
    rec = records[0]
    assert rec["image_id"] == "img_fox_01"
    assert rec["subject"] == "Red Fox"
    assert rec["attributes"] == ["red coat", "white chest"]
    assert rec["embedding"] == vector


def test_save_image_record_upsert():
    """Verify save_image_record updates existing record on duplicate primary key."""
    save_image_record(
        image_id="img_fox_01",
        file_path="assets/fox_v1.jpg",
        subject="Red Fox",
        category="fox",
        attributes=["v1"],
        caption="Original caption text for red fox",
        confidence=0.80,
        tokens_consumed=1000,
        cost_usd=0.00010
    )

    # Update with new values
    save_image_record(
        image_id="img_fox_01",
        file_path="assets/fox_v2.jpg",
        subject="Red Fox",
        category="fox",
        attributes=["v2", "updated"],
        caption="Updated caption text for red fox",
        confidence=0.95,
        tokens_consumed=1500,
        cost_usd=0.00020
    )

    save_image_embedding("img_fox_01", [0.5, 0.5])
    records = get_all_images_with_embeddings()
    assert len(records) == 1
    assert records[0]["file_path"] == "assets/fox_v2.jpg"
    assert records[0]["confidence"] == 0.95
    assert records[0]["attributes"] == ["v2", "updated"]


def test_log_and_update_review_ledger():
    """Verify logging audit actions and updating status in review ledger."""
    entry_id = log_review_action(
        post_id="post_99",
        image_id="img_wolf_01",
        score=0.88,
        guard_status="APPROVED",
        explanation="Matched successfully",
        status="PENDING"
    )
    assert entry_id > 0

    ledger_before = fetch_review_ledger()
    assert len(ledger_before) == 1
    assert ledger_before[0]["status"] == "PENDING"

    # Update status to APPROVED
    updated = update_review_status(post_id="post_99", image_id="img_wolf_01", action="APPROVED")
    assert updated is True

    ledger_after = fetch_review_ledger()
    assert len(ledger_after) == 1
    assert ledger_after[0]["status"] == "APPROVED"


def test_update_review_status_non_existent():
    """Verify update_review_status returns False when post_id/image_id is not found."""
    updated = update_review_status(post_id="non_existent", image_id="none", action="REJECTED")
    assert updated is False


def test_fetch_cost_telemetry():
    """Verify cost telemetry logs retrieve correct financial and token metrics."""
    save_image_record(
        image_id="asset_t1",
        file_path="assets/t1.jpg",
        subject="Bear",
        category="bear",
        attributes=["grizzly"],
        caption="A grizzly bear catching salmon",
        confidence=0.91,
        tokens_consumed=2000,
        cost_usd=0.0003
    )

    telemetry = fetch_cost_telemetry()
    assert len(telemetry) == 1
    item = telemetry[0]
    assert item["image_id"] == "asset_t1"
    assert item["tokens_consumed"] == 2000
    assert item["cost_usd"] == 0.0003
