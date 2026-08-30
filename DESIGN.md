# 🦊 AI Image Understanding & Content Matching Engine — Architecture & Design Document

## 1. Problem Statement & Mission
**Problem:** Automated CMS platforms frequently misallocate visual assets to articles because they rely on fragile, manual keyword string-matching or literal file-naming conventions (e.g., matching a post containing the word "fox" to a picture of a "wolf" because the file was poorly labeled).

**Solution:** Build a deterministic backend system that:
- Extracts structured semantic profiles from image payloads using a multimodal vision model (Gemini 2.5 Flash).
- Executes mathematical vector comparisons against target articles using local sentence-transformer embeddings (`all-MiniLM-L6-v2`).
- Implements an explicit **Mismatch Guard** that prioritizes *safe rejection* over an inaccurate match.

**Core Philosophy:** Treat the AI model as an unreliable data-parsing component, and wrap it in rigid, traditional engineering constraints — schemas, rate limiters, and vector math. The goal is to transition from building "AI wrappers" to designing **deterministic AI systems**.

---

## 2. Core Constraints & Non-Goals
- **In-Scope:**
  - Strict schema validation on all visual analyses (Pydantic boundary schemas with confidence floor >= 0.75).
  - $0 infrastructure footprint (local vector embeddings, local SQLite datastore).
  - Strict local execution engine for vector comparisons (`numpy` cosine similarity).
  - Isolated API credentials via `.env`.
- **Explicit Non-Goals:**
  - Not an image search engine, asset gallery explorer, bulk tagging manager, or frontend application.
  - Backend API decision engine only.

---

## 3. Data Model Schema
```json
{
  "asset_id": "string (UUID or file hash)",
  "file_path": "string",
  "visual_profile": {
    "exact_subject": "string",
    "category": "string",
    "attributes": ["string"],
    "literal_description": "string",
    "confidence": "float"
  },
  "processing_metadata": {
    "tokens_consumed": "integer",
    "estimated_cost_usd": "float",
    "timestamp": "string (ISO 8601)"
  }
}
```

---

## 4. API Surface Layout
- `GET /posts/{id}/images` — retrieves ranked and mismatch-guarded image suggestions for a specific post.
- `POST /review/action` — Human-in-the-loop endpoint to approve or reject a suggested match.
- `GET /review/ledger` — exposes the internal audit logging registry for manual evaluation sweeps.
- `GET /health` — healthcheck status endpoint.

---

## 5. System Architecture Diagram
```
Images → (Batch Worker Queue) → Gemini 2.5 Flash → Schema Verified JSON → Local Embedding
                                                                               |
                                                                               v
Posts ───────────────────────────→ Sentence-Transformers (all-MiniLM-L6-v2) → Vector Match
                                                                               |
                                                                               v
                                                         [ THE MISMATCH GUARD ]
                                                           ├── Tag Cross-Check
                                                           └── Similarity Threshold Gate (>= 0.54)
                                                                               |
                                                                               v
                                                     Outputs: Confident Match OR Safe Rejection
```

---

## 6. The Three Genuinely Hard Parts
1. **Schema validation & rejection** — never trust raw text output from a multimodal model. Force structured JSON output; on parse failure or confidence score < 0.75, route to an isolation queue rather than guessing.
2. **Tuning the Guard** — precision requires empirical threshold sweeping. Build a labeled validation set (true matches + deceptive near-misses like wolf/dog), sweep thresholds from `0.40` to `0.65`, and optimize precision score.
3. **Batch discipline (rate limits & token metrics)** — handle batch processing with exponential backoff and track financial token consumption per API call ($0.000075 / 1k input tokens, $0.0003 / 1k output tokens).

---

## 7. Phased Execution Matrix
| Stage | Milestone Objective | Required Deliverable Gate |
|---|---|---|
| **1. Design & Setup** | Specs, manifest, environment configuration | `DESIGN.md`, `capstone.yaml`, `.env.example` signed off |
| **2. Pipeline & Data** | Pydantic boundary schemas & SQLite engine | `schemas.py`, `database.py` implemented |
| **3. Ingestion & Seed** | Batch worker, token cost telemetry, seed dataset | `seed.py` seeded with telemetry logged |
| **4. Matching Engine** | Sentence-transformer vector engine + Mismatch Guard | `services.py` with refusal logic |
| **5. Eval Sweep** | Precision sweep & empirical threshold pinpointing | `eval_suite.py`, `EVIDENCE.md` updated |
| **6. API & Tests** | FastAPI production endpoints & Pytest test suite | `main.py`, `test_engine.py`, `README.md` green |
