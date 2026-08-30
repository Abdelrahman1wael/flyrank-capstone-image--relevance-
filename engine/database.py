"""
SQLite Database Infrastructure for the AI Image Understanding & Content Matching Engine.
"""

import os
import json
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

DB_FILE = os.getenv("DATABASE_URL", "sqlite:///flyrank_cms.db").replace("sqlite:///", "")


def get_db_connection() -> sqlite3.Connection:
    """Creates a sqlite3 connection with Row factory enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initializes schema tables in SQLite if they do not exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Images table storing structural profiles & financial token cost telemetry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                image_id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                subject TEXT NOT NULL,
                category TEXT NOT NULL,
                attributes_json TEXT NOT NULL,
                caption TEXT NOT NULL,
                confidence REAL NOT NULL,
                tokens_consumed INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0,
                created_at TEXT NOT NULL
            );
        """)

        # Vector embeddings table storing serialized JSON arrays
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_embeddings (
                image_id TEXT PRIMARY KEY,
                embedding_json TEXT NOT NULL,
                FOREIGN KEY (image_id) REFERENCES images(image_id) ON DELETE CASCADE
            );
        """)

        # Posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                post_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)

        # Human-in-the-loop audit review ledger table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT NOT NULL,
                image_id TEXT NOT NULL,
                score REAL NOT NULL,
                guard_status TEXT NOT NULL,
                explanation TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                timestamp TEXT NOT NULL
            );
        """)

        conn.commit()


def save_image_record(
    image_id: str,
    file_path: str,
    subject: str,
    category: str,
    attributes: List[str],
    caption: str,
    confidence: float,
    tokens_consumed: int,
    cost_usd: float
) -> None:
    """Inserts or updates an image record in the database."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO images (
                image_id, file_path, subject, category, attributes_json,
                caption, confidence, tokens_consumed, cost_usd, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            image_id, file_path, subject, category, json.dumps(attributes),
            caption, confidence, tokens_consumed, cost_usd, now_iso
        ))
        conn.commit()


def save_image_embedding(image_id: str, embedding_vector: List[float]) -> None:
    """Inserts or updates an image's vector embedding in SQLite."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO image_embeddings (image_id, embedding_json)
            VALUES (?, ?)
        """, (image_id, json.dumps(embedding_vector)))
        conn.commit()


def get_all_images_with_embeddings() -> List[Dict[str, Any]]:
    """Fetches all indexed images along with their vector embeddings."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.image_id, i.file_path, i.subject, i.category, i.attributes_json,
                   i.caption, i.confidence, i.tokens_consumed, i.cost_usd, e.embedding_json
            FROM images i
            INNER JOIN image_embeddings e ON i.image_id = e.image_id
        """)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            record = dict(row)
            record["attributes"] = json.loads(record["attributes_json"])
            record["embedding"] = json.loads(record["embedding_json"])
            result.append(record)
        return result


def log_review_action(
    post_id: str,
    image_id: str,
    score: float,
    guard_status: str,
    explanation: str,
    status: str = "PENDING"
) -> int:
    """Logs a matching decision into the review ledger for audit."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO review_ledger (post_id, image_id, score, guard_status, explanation, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (post_id, image_id, score, guard_status, explanation, status, now_iso))
        conn.commit()
        return cursor.lastrowid


def update_review_status(post_id: str, image_id: str, action: str) -> bool:
    """Updates status for human review workflow."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE review_ledger SET status = ? WHERE post_id = ? AND image_id = ?
        """, (action, post_id, image_id))
        conn.commit()
        return cursor.rowcount > 0


def fetch_review_ledger() -> List[Dict[str, Any]]:
    """Retrieves all entries in the review audit ledger."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM review_ledger ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def fetch_cost_telemetry() -> List[Dict[str, Any]]:
    """Retrieves token and cost telemetry for all visual processing jobs."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT image_id, file_path, subject, confidence, tokens_consumed, cost_usd FROM images")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
