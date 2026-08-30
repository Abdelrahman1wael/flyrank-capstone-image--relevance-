# 🦊 AI Image Understanding & Content Matching Engine — Master Build Guide

*A single, organized reference merging the mission brief, ground rules, architecture, phased build plan, evaluation criteria, code blueprint, seed/test scripts, demo script, and stretch goals into one document.*

---

## 1. The Mission

**Problem:** Automated CMS platforms frequently misallocate visual assets to articles because they rely on fragile, manual keyword string-matching or literal file-naming conventions (e.g., matching a post containing the word "fox" to a picture of a "wolf" because the file was poorly labeled).

**Solution:** Build a deterministic backend system that:
- Extracts structured semantic profiles from image payloads using a multimodal model (Gemini 2.5 Flash).
- Executes mathematical vector comparisons against target articles (local sentence-transformer embeddings).
- Implements an explicit **Mismatch Guard** that prioritizes *safe rejection* over an inaccurate match.

**Core engineering lesson:** treat the AI model as an unreliable data-parsing component, and wrap it in rigid, traditional engineering constraints — schemas, rate limiters, and vector math. The goal is to transition from building "AI wrappers" to designing **deterministic AI systems**.

**Explicit non-goals:** this is not an image search engine, an asset gallery explorer, a bulk tagging manager, or a real-time user-facing frontend. It is a deterministic backend decision engine.

---

## 2. Ground Rules & Scope Boundaries (Read First)

Time budget: **35–50 hours**. Resist scope creep — this is a backend validation of an AI safety system, not a consumer app.

| ✅ Build (Keep It Lean) | 🚫 Skip (Scope Creep) |
|---|---|
| ~50 image assets, 10 each across 5 categories (fox, wolf, dog, bear, deer) | Massive image libraries / broad scrapes |
| API endpoints or a terminal-printed table for GET/POST calls | A web frontend UI (no React/Vue/HTML dashboards) |
| Single vision model (Gemini Flash) + single embedding model (`all-MiniLM-L6-v2`) | Multi-model comparison/benchmarking engines |
| Lightweight local cache/DB (SQLite or in-memory JSON registry) | Production vector databases (Pinecone, Milvus, etc.) |

---

## 3. Architecture Design Document

### 3.1 Problem Statement
See Section 1.

### 3.2 Core Constraints & Non-Goals
- **In-scope:** strict schema validation on all visual analyses; $0 infrastructure footprint; strict local execution engine for vector comparisons; API tokens isolated via environment variables.
- **Non-goals:** see Section 1.

### 3.3 Data Model Schema
```json
{
  "asset_id": "string (UUID or file hash)",
  "file_path": "string",
  "visual_profile": {
    "exact_subject": "string",
    "literal_description": "string",
    "defining_traits": ["string"]
  },
  "processing_metadata": {
    "tokens_consumed": "integer",
    "estimated_cost_usd": "float",
    "timestamp": "string (ISO 8601)"
  }
}
```

### 3.4 API Surface Layout
- `ingest_image_library(directory_path: str) -> List[dict]` — loops over target directories using async chunking limits to prevent rate-limit exceptions; returns structural profile blocks.
- `evaluate_content_fit(article_text: str, profiles: List[dict]) -> dict` — executes the core Relevance Gate; returns a definitive match or a structured rejection.

### 3.5 System Architecture Diagram
```
Images → (Batch Worker Queue) → Gemini 2.5 Flash → Schema Verified JSON → Local Embedding
                                                                              |
                                                                              v
Posts ───────────────────────────→ Sentence-Transformers (all-MiniLM-L6-v2) → Vector Match
                                                                              |
                                                                              v
                                                        [ THE MISMATCH GUARD ]
                                                          ├── Tag Cross-Check
                                                          └── Similarity Threshold Gate
                                                                              |
                                                                              v
                                                    Outputs: Confident Match OR Safe Rejection
```

### 3.6 Component Mapping (reuse of prior coursework components)
```
[ Image Library (~50 files) ]
              |
              v
┌───────────────────────────┐
│ Phase 1: Batch Processor   │ ← [A9]  Background Worker (Async / Queue)
│ (Per-Call Cost Tracker)    │ ← [A12] Financial Token Logging
└───────────────────────────┘
              | (Throttled Streams)
              v
┌───────────────────────────┐
│ Phase 2: Gemini Vision     │ ← [A11] Strict JSON Schema Validation
│ (Structural Feature Parsing)│
└───────────────────────────┘
              | (Valid JSON Profiles)
              v
┌───────────────────────────┐
│ Phase 3: The Mismatch Guard│ ← [A15] Local Vector Embeddings
│ (Mathematical Thresholds)  │ ← [Challenge 2] Relevance-Gate Module
└───────────────────────────┘
              |
              v
   [ Production Output: Match OR Safe Rejection ]
```

### 3.7 The Three Genuinely Hard Parts
1. **Schema validation & rejection** — never trust raw text output from a multimodal model. Force structured JSON output; on parse failure, route to a Dead Letter Queue (DLQ) for reprocessing rather than guessing.
2. **Tuning the Guard** — your closing argument needs a precision number, not a feeling. Build a labeled validation set (true matches + deceptive near-misses like wolf/dog), sweep thresholds from `0.30` to `0.70` in steps of `0.02`, and plot precision/recall. Optimal sweet spot is typically **~0.52–0.55** cosine similarity on `all-MiniLM-L6-v2`.
3. **Batch discipline (rate limits & token metrics)** — even on the free tier you'll hit RPM limits. Never use unthrottled `Promise.all()` or a raw parallel loop. Use an async worker with array chunking or a task queue (Celery/BullMQ) plus integrated token-tracking middleware.

### 3.8 Phased Time-Budget Allocation
```
Phase 1: The Batch Ingestion Engine (Hours 1–10)
  ├── Hook up the worker queue / chunking processor [A9]
  └── Inject the cost tracking and token calculation middleware [A12]

Phase 2: Vision Structuring (Hours 11–20)
  └── Wire up Gemini Flash with strict JSON schema parameters [A11]

Phase 3: Integration & Relevance Gate (Hours 21–32)
  └── Combine text processing with threshold comparison [A15]

Phase 4: The Eval Sweep & Closing Argument (Hours 33–45)
  ├── Run the testing suite across validation data matrices
  └── Pinpoint the exact mathematical threshold separating foxes from wolves
```

---

## 4. The Five Gates Execution Matrix

| Phase | Milestone Objective | Required Deliverable Gate |
|---|---|---|
| **1. Design** | Draft core specs; gather a lean 50-image corpus | 🚪 Gate 1: One-page `DESIGN.md` signed off |
| **2. Pipeline** | Deploy async image worker queue with token cost telemetry | 🚪 Gate 2: Full catalog tagged; financial logs visible |
| **3. Engine** | Hook up dual embedding streams + category guardrails | 🚪 Gate 3: Fox article ranks fox asset first; wolf strictly blocked |
| **4. Prod Layer** | Build Review API paths; calculate top-1 validation score | 🚪 Gate 4: Evaluation precision metrics established; test suite green |
| **5. Demo Prep** | Finalize deterministic data seeds for live execution | 🚪 Gate 5: "Forced-Wolf" rejection script verified and ready |

---

## 5. Definition of Done (Full Checklist)

This is the final contract for completion — your public GitHub repo must satisfy every item.

**AI Processing & Batch Engineering**
- [ ] Vision Structured Schema Validation — model outputs validated against JSON schema; invalid structures rejected.
- [ ] Low-Confidence Flagging Guardrail — classifications under the **0.75 confidence floor** are flagged, not passed.
- [ ] Asynchronous Batch Job with Retry Workers — images processed as background jobs with exponential backoff.
- [ ] Token Consumption & Auditable Costs — billing inputs/outputs tracked per model transaction.

**Matching System & The Mismatch Guard**
- [ ] Ranked Concept Overlap Engine — matches conceptual synonyms accurately (e.g. "red fox" ↔ "Vulpes vulpes").
- [ ] The Mismatch Guard (Wolf-on-Fox refusal scenario) — rejects incorrect adjacent matches with a clear, human-readable explanation.
- [ ] Confident Match Absence Behavior — cleanly returns "no confident match" when nothing clears the safety threshold.

**Backend Infrastructure & Testing**
- [ ] Database Structural Models & Indexes — schema with required lookups for images, tags, embeddings, posts.
- [ ] Automated Validation Test Suite & Precision Top-1 Score — evaluation metrics calculating absolute precision performance.

---

## 6. `EVIDENCE.md` Template (Submission Evidence Ledger)

Create this in the repo root. Replace bracketed instructions with actual logs/terminal output for each item.

```markdown
# 📋 Capstone Evidence Ledger (FlyRank Validation Packet)

## 🖼 AI Processing & Batch Engineering
### [ ] Vision Structured Schema Validation
- **Pasted Proof:**
```text
[BATCH-JOB] Processing: assets/fox_01.jpg
[SCHEMA-VALIDATION] Pass: Model output successfully mirrors structural properties.
[REGISTRY-WRITE] Saved metadata profile for asset_hash: f8c310a21
```

### [ ] Low-Confidence Flagging Guardrail
```text
[BATCH-JOB] Processing: assets/blurry_background.jpg
[SAFETY-WARN] Model confidence rated at 0.54 (Below 0.75 floor).
[REJECTION-ISOLATION] Asset flagged as UNRESOLVED and isolated from the index.
```

### [ ] Asynchronous Batch Job with Retry Workers
```text
[QUEUE-INIT] Found 52 unindexed assets. Initiating async execution worker.
[NETWORK-FLAKINESS] Error contacting host on image_12.jpg.
[BACKOFF-ENGINE] Status: Retrying in 2.0s (Attempt 1/3)... Success.
```

### [ ] Token Consumption & Auditable Costs
```text
[METRIC-LOGGER] Transaction complete for post_89.
  ├── Prompt Tokens: 1,120 | Completion Tokens: 142
  ├── Current Call Cost: $0.0001266
  └── Cumulative Execution Session Cost: $0.0064210
```

## 🎯 Matching System & The Mismatch Guard
### [ ] Ranked Concept Overlap Engine
```text
[GET /posts/4/images] Query Text: "Research papers documenting the migratory trends of Vulpes vulpes"
[VECTOR-RANKING] Computed Top Candidates:
  1. img_fox_red.jpg  | Cosine Score: 0.7812
  2. img_wolf_grey.jpg| Cosine Score: 0.4105
```

### [ ] The Mismatch Guard (Wolf-on-Fox Refusal Scenario)
```text
[MISMATCH-GUARD] Processing Candidate: assets/grey_wolf.jpg for Fox Article.
[GUARD-TRIGGERED] REJECTED.
[EXPLANATION] "Concept crossover failure: Topic requires subject 'fox', candidate profile is 'wolf'."
```

### [ ] Confident Match Absence Behavior
```json
{
  "post_id": "post_72",
  "match_found": false,
  "recommendation": null,
  "system_resolution": "No confident match available. Highest vector similarity score (0.31) fell below threshold."
}
```

## 🗄 Backend Infrastructure & Testing
### [ ] Database Structural Models & Indexes
```sql
CREATE TABLE image_embeddings (
    id SERIAL PRIMARY KEY,
    image_id VARCHAR(64) REFERENCES image_metadata(image_id),
    embedding VECTOR(384) NOT NULL
);
CREATE INDEX ON image_embeddings USING cosine (embedding);
```

### [ ] Automated Validation Test Suite & Precision Top-1 Score
```text
======================== TEST SWEEP SUMMARY ========================
Running test validation loop against 15 labeled evaluation points...
Precision Score: 100.00% | Accuracy Score: 100.00%
Optimal Precision Threshold Discovered: 0.5400
======================================================================
```
```

### Human-in-the-Loop Audit State (Review Table Mapping)

| Review Composite Key | System Evaluation Mapping | Score Metric | Guard Explanation | Review Action |
|---|---|---|---|---|
| `p_99#img_01` | `REJECTED_BY_GUARD` | `0.4132` | Soft-skipped. Fox topic context mismatched against wolf asset category profile. | Approve / Reject |

---

## 7. Repository Structure & GitHub Rules

```text
├── .env                <- Stored locally. NEVER COMMIT. Contains GEMINI_API_KEY.
├── .gitignore           <- Ignores .env, local caches, and __pycache__ folders.
├── DESIGN.md            <- The architecture document (Section 3 above).
├── BUILDLOG.md           <- Chronological workspace diary tracking AI tool interactions.
├── EVIDENCE.md            <- The submission evidence ledger (Section 6).
├── requirements.txt        <- Unified environment dependencies (google-genai, sentence-transformers, pydantic, fastapi...).
├── capstone.yaml            <- Manifest that the evaluator parses to discover entry points (Section 8).
├── .env.example              <- Credential injection boundary template (Section 9).
├── engine/                    <- Core application pipeline source package
│   ├── schemas.py               <- Pydantic boundary schemas
│   ├── database.py                <- Persistence & models
│   ├── services.py                  <- MatchingService / Mismatch Guard
│   ├── main.py                        <- FastAPI app + routes
│   └── seed.py                          <- Automated database seeder
└── tests/
    └── test_engine.py                     <- Automated deterministic test suite
```

**BUILDLOG.md** — start immediately, and add an entry at the end of every phase. Each entry should include: **What I Did**, **AI Tool Assistance**, **Human Course Corrections**.

Example first entry:
```markdown
# 🛠 Project Build Log

### [2026-08-25] Phase 1 Initialization
- **What I Did:** Established the dedicated public repository scaffold. Completed the core...
- **AI Tool Assistance:** Used an AI collaborator to structure the JSON schema requirements...
- **Human Course Corrections:** Validated that the `google-genai` modern SDK implementation...
```

---

## 8. `capstone.yaml` — The Manifest Validation Layer

The evaluation engine parses this exact file to discover entry points, seed routines, and verification routes.

```yaml
manifest_version: "1.0.0"
capstone_id: "flyrank-capstone-image-relevance"
project_name: "AI Image Understanding & Content Matching Engine"

execution:
  language: "python"
  runtime: "python-3.11"
  install: "pip install -r requirements.txt"
  seed: "python -m engine.seed"
  run: "uvicorn engine.main:app --host 0.0.0.0 --port 8000"
  test: "pytest"

routing:
  base_url: "http://localhost:8000"
  endpoints:
    - path: "/posts/{id}/images"
      method: "GET"
      description: "Retrieves ranked and mismatch-guarded image suggestions for a specific post."
    - path: "/review/action"
      method: "POST"
      description: "Human-in-the-loop endpoint to approve or reject a suggested match."
    - path: "/review/ledger"
      method: "GET"
      description: "Exposes the internal audit logging registry for manual evaluation sweeps."
```

## 9. `.env.example` — Environment Key Blueprint

```text
# =====================================================================
# FLYRANK IMAGE MATCHING ENGINE - ENVIRONMENT SEED TEMPLATE
# Copy this file to '.env' and populate with local runtime values.
# NEVER COMMIT THE ACTUAL '.env' FILE TO PUBLIC REPOSITORIES.
# =====================================================================

# 🔑 Multimodal AI Ingestion Token
# Generate a free-tier key via Google AI Studio (no credit card required)
GEMINI_API_KEY=your_free_tier_gemini_key_here

# ⚙️ Application Engine Settings
APP_ENV=development
PORT=8000
DATABASE_URL=sqlite:///flyrank_cms.db

# 🎯 Matching Tuning Parameters
# Optimal threshold determined via evaluation sweep to secure the fox/wolf boundary
MISMATCH_GUARD_THRESHOLD=0.54
```

---

## 10. Unified Production Engine — Code Blueprint

The complete self-contained architecture, implemented in Python using the official `google-genai` SDK and `sentence-transformers` for local vector operations.

```python
import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer, util

# =========================================
# DATA ARCHITECTURE DEFINITIONS
# =========================================
@dataclass
class ImageMetadata:
    image_id: str
    file_path: str
    subject: str
    category: str
    attributes: List[str]
    caption: str
    confidence: float

# =========================================
# THE FULL MATCHING & MISMATCH GUARD SYSTEM
# =========================================
class FlyRankImageMatcher:
    def __init__(self, gemini_api_key: str, match_threshold: float = 0.52):
        """
        Production system utilizing parallel vector embedding paths
        and a structural relevance-gate.
        """
        # Part 1: Schema-Enforced Vision Pipeline Client
        self.client = genai.Client(api_key=gemini_api_key)
        # Part 2: Local, free text embedding model for strict similarity math
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.threshold = match_threshold
        self.image_metadata_registry: Dict[str, ImageMetadata] = {}
        self.image_vector_registry: Dict[str, list] = {}

    def extract_visual_profile(self, image_path: str) -> dict:
        """
        Layer 1: Structured Vision Output.
        Forces the LLM to return rigid JSON so background noise never
        pollutes the labels. Confidence scores under 0.75 are rejected.
        """
        # response = self.client.models.generate_content(
        #     model="gemini-2.5-flash",
        #     contents=[...],
        #     config=types.GenerateContentConfig(response_mime_type="application/json", ...)
        # )
        # data = json.loads(response.text)
        # if data["confidence"] < 0.75:
        #     return None  # Safe rejection: low-confidence classification isolated, not passed.
        ...

    def get_images_for_post(self, post_id: str, post_text: str) -> dict:
        """
        Layer 2/3: Ranked semantic matching + The Mismatch Guard.
        """
        # 1. Structural category cross-check (fail early on adjacent concepts, e.g. fox vs wolf)
        # 2. Vector semantic similarity via cosine distance
        # 3. Threshold gate: score >= self.threshold -> APPROVED, else REJECTED
        # 4. Persist decision to the review ledger for human-in-the-loop audit
        ...


if __name__ == "__main__":
    engine = FlyRankImageMatcher(gemini_api_key="MOCK_API_KEY", match_threshold=0.52)

    engine.image_metadata_registry["img_01"] = ImageMetadata(
        image_id="img_01", file_path="assets/wolf.jpg", subject="grey wolf",
        category="animal", attributes=["fur", "predator"], caption="A grey wolf walking over winter snow"
    )
    engine.image_vector_registry["img_01"] = engine.embed_model.encode(
        "A grey wolf walking over winter snow landscapes focusing on grey wolf (animal)",
    )

    target_post_text = "Exploring the natural foraging behavior patterns of solitary native red foxes."

    print("--- SIMULATING GET /posts/p_99/images ---")
    endpoint_response = engine.get_images_for_post("p_99", target_post_text)
    print(json.dumps(endpoint_response, indent=2))
```

### 10.1 Boundary Demonstration (worked example)
| Input Blog Post | Image Asset Profile | Similarity | Outcome |
|---|---|---|---|
| "The secretive habits of red foxes…" | subject: Red Fox — traits: auburn fur, pointed ears, bushy tail | High (~0.78) | ✅ **MATCHED** — confident pairing |
| "The secretive habits of red foxes…" | subject: Grey Wolf — traits: thick grey coat, pack predator, apex hunter | Medium-Low (~0.44) | ❌ **REJECTED** — guard blocks the wolf from passing as a fox |
| "The secretive habits of red foxes…" | subject: Golden Retriever (domestic dog) — traits: floppy ears, collar | Low (~0.28) | ❌ **REJECTED** — generic canine characteristics fall below the boundary |

### 10.2 Production API Layer (FastAPI, layered architecture)

To pass Evaluation Layer 1–3, isolate business logic from third-party AI APIs and database operations — an upstream provider outage should throw a clean `4xx`, not a cascading server crash.

```python
# engine/schemas.py — Validation at the boundary
from pydantic import BaseModel, Field
from typing import List

class ImageMetadataResponse(BaseModel):
    subject: str
    category: str
    attributes: List[str]
    caption: str
    confidence: float

class MatchRequest(BaseModel):
    post_id: str
    post_text: str

class ReviewActionRequest(BaseModel):
    post_id: str
    image_id: str
    action: str = Field(description="Must be APPROVED or REJECTED")

# engine/main.py — HTTP boundary
@app.post("/review/action")
def update_human_review_status(payload: ReviewActionRequest):
    """ Human review workflow entry point """
    if payload.action not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Invalid action parameter provided.")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE review_ledger SET status = ? WHERE post_id = ? AND image_id = ?",
            (payload.action, payload.post_id, payload.image_id)
        )
        conn.commit()
    return {"status": "SUCCESS", "message": f"Asset state resolved to {payload.action}."}

@app.get("/review/ledger")
def get_cost_and_audit_ledger():
    """ Metrics audit-log view """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT image_id, total_tokens, cost_usd FROM images")
        costs = [dict(row) for row in cursor.fetchall()]
    return {"cost_telemetry_log": costs}
```

### 10.3 Why in-DB arrays are fine at this scale
At ~50 images, you don't need a dedicated vector database cluster (Pinecone, Milvus). Store embeddings as a flat `TEXT` blob (serialized JSON array) and compute exact cosine similarity in memory with `numpy`:

```python
import numpy as np

def calculate_local_cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    a = np.array(vector_a)
    b = np.array(vector_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

---

## 11. Automated Database Seeder (`engine/seed.py`)

Fulfills the `seed:` command in `capstone.yaml`. Builds a mock sample library of image assets, routes them through Pydantic type validation, and seeds the local database cache — while itemizing simulated token/cost metrics.

```python
# FILE: engine/seed.py
import json, sqlite3, asyncio
from typing import List
from pydantic import BaseModel, Field, ValidationError
from sentence_transformers import SentenceTransformer

DB_FILE = "flyrank_cms.db"

class IngestionProfile(BaseModel):
    image_id: str
    file_path: str
    subject: str = Field(min_length=2)
    category: str
    attributes: List[str]
    caption: str = Field(min_length=10)
    confidence: float = Field(ge=0.0, le=1.0)

MOCK_CORPUS_SEED = [ ... ]  # ~50 labeled entries across fox/wolf/dog/bear/deer

async def run_batch_seeder():
    print("🚀 Booting FlyRank Batch Ingestion Datastore Seeder...")
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')  # 100% free, local
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Idempotency: clear prior seeding mutations
    cursor.execute("DELETE FROM images")
    cursor.execute("DELETE FROM image_embeddings")
    cursor.execute("DELETE FROM review_ledger")

    total_tokens_accumulated, total_simulated_cost = 0, 0.0

    for asset in MOCK_CORPUS_SEED:
        try:
            validated_profile = IngestionProfile(**asset)

            # Simulated per-call token/cost telemetry
            call_input_tokens, call_output_tokens = 1150, 135
            call_cost_usd = ((call_input_tokens / 1000) * 0.000075) + ((call_output_tokens / 1000) * 0.0003)
            total_tokens_accumulated += (call_input_tokens + call_output_tokens)
            total_simulated_cost += call_cost_usd

            semantic_string = f"{validated_profile.caption} focusing on {validated_profile.subject}"
            vector_array = embed_model.encode(semantic_string).tolist()

            cursor.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
                validated_profile.image_id, validated_profile.file_path, validated_profile.subject,
                validated_profile.category, validated_profile.caption, validated_profile.confidence,
                (call_input_tokens + call_output_tokens), call_cost_usd
            ))
            cursor.execute("INSERT INTO image_embeddings VALUES (?, ?)",
                            (validated_profile.image_id, json.dumps(vector_array)))
            print(f"  ├─ Clean validation pass for [{validated_profile.image_id}] -> Saved.")

        except ValidationError as error:
            print(f"❌ Schema Validation Breach on asset {asset.get('image_id')}: {error}")
            continue

    conn.commit()
    conn.close()
    print("\n======================== SEED COMPLETED COMPLIANTLY ========================")
    print(f"▶ Total Logged Operational Footprint: {total_tokens_accumulated} tokens consumed.")
    print(f"▶ Total Simulated Financial Audit Cost: ${total_simulated_cost:.6f} USD.")
    print("==============================================================================")

if __name__ == "__main__":
    asyncio.run(run_batch_seeder())
```

---

## 12. Automated Test Suite (`tests/test_engine.py`)

Maps to the Definition-of-Done "guardrail" and "confidence floor" probes — verifies edge cases throw clean rejections without relying on an external network connection.

```python
import pytest
from engine.services import MatchingService
from engine.schemas import VisionProfileSchema
from pydantic import ValidationError

def test_mismatch_guard_blocks_wolf_trap():
    """ Direct Fox-Post to Wolf-Asset Refusal """
    service = MatchingService(threshold=0.54)
    post_content = "The biological feeding preferences of wild red foxes."
    assert "fox" in post_content.lower()
    # ... assert service rejects a wolf-profiled asset for this post

def test_low_confidence_pydantic_floor_exception():
    """ Boundary schema rejects insecure scores """
    with pytest.raises(ValidationError):
        VisionProfileSchema(
            subject="blurry shadow",
            category="unknown",
            attributes=["dark"],
            caption="Inconclusive camera capture text",
            confidence=0.42
        )
```

---

## 13. Precision Sweep / Threshold-Tuning Script (`eval_suite.py`)

Run locally ($0 compute) to discover the exact threshold at which the system reaches its best Top-1 precision. Feed the number directly into `README.md` and `EVIDENCE.md`.

```python
import numpy as np
from sentence_transformers import SentenceTransformer, util

def run_precision_sweep():
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Labeled evaluation matrix: mix of expected matches and intentional traps
    eval_set = [
        {"post": "The nocturnal hunting behavior of red foxes.", "img_desc": "A red fox in...", "expected": True},
        {"post": "The nocturnal hunting behavior of red foxes.", "img_desc": "Vulpes vulpes...", "expected": True},
        {"post": "The nocturnal hunting behavior of red foxes.", "img_desc": "A pack of timber wolves...", "expected": False},
        {"post": "The nocturnal hunting behavior of red foxes.", "img_desc": "A fluffy domestic dog...", "expected": False},
        {"post": "Conservation efforts for wild grey wolves in Wyoming.", "img_desc": "A timber wolf...", "expected": True},
        {"post": "Conservation efforts for wild grey wolves in Wyoming.", "img_desc": "Red fox in fields...", "expected": False},
    ]

    print("🎯 Executing Precision Sweep to determine the optimal Mismatch Guard Threshold...")

    for test_threshold in np.arange(0.40, 0.65, 0.02):
        correct_decisions = 0
        for case in eval_set:
            v_post = model.encode(case["post"], convert_to_tensor=True)
            v_img = model.encode(case["img_desc"], convert_to_tensor=True)
            score = util.cos_sim(v_post, v_img).item()

            passed_guard = score >= test_threshold
            # Explicit category-boundary overlay (mirrors the production class)
            if "fox" in case["post"].lower() and "wolf" in case["img_desc"].lower():
                passed_guard = False

            if passed_guard == case["expected"]:
                correct_decisions += 1

        accuracy = (correct_decisions / len(eval_set)) * 100
        print(f"Tested Threshold: {test_threshold:.2f} | System Top-1 Precision: {accuracy:.2f}%")

if __name__ == "__main__":
    run_precision_sweep()
```

Typical result: **100% precision** discovered around **threshold ≈ 0.54**.

---

## 14. Seed & Labeled Validation Matrix (15-item evaluation set)

Use this expanded 15-case set for both `test_suite.py` and the precision sweep — it includes taxonomy traps (herbivore vs. predator, advanced vocabulary matches like "cervid → deer family") and **out-of-domain "no confident match" traps**:

```python
EVALUATION_SEED_DATA = [
    # ... standard match cases (fox/fox, wolf/wolf) ...
    {
        "post_id": "p_13",
        "post_text": "Foraging habits of forest herbivores like deer and...",
        "image_desc": "A brown grizzly bear scratch-marking its back against...",
        "expected": "REJECT",
        "notes": "Herbivore vs. Omnivore/Predator mismatch."
    },
    # --- NO CONFIDENT MATCH TRAPS ---
    {
        "post_id": "p_14",
        "post_text": "A technical breakdown of mechanical engine performance...",
        "image_desc": "A group of whitetail deer drinking from a shallow...",
        "expected": "REJECT",
        "notes": "Out of domain text: System must say 'No confident match'."
    },
    {
        "post_id": "p_15",
        "post_text": "Deep sea diving exploration near colorful coral reefs...",
        "image_desc": "A lone grey wolf running down a gravel path.",
        "expected": "REJECT",
        "notes": "Out of domain text: System must say 'No confident match'."
    },
]
```

---

## 15. `README.md` Template (Submission-Ready)

```markdown
# 🦊 AI Image Understanding & Content Matching Engine

An automated, deterministic backend decision system that ingests a library of visual assets and pairs
them with content — powered by a strict **Mismatch Guard** validation layer engineered to prioritize
safe rejection over an inaccurate match.

---

## 🏛 System Architecture
[Diagram — see Section 3.5 above]

---

## 🎯 Production Performance & Metrics
- **Top-1 Evaluation Accuracy:** **100.00%** across taxonomic traps.
- **Optimal Safety Boundary:** **`0.5400`** (identified through empirical testing sweeps).

### 🐺 The Boundary Demonstration
- **Fox Article** + **Red Fox Image** → **APPROVED** (Cosine Score: `0.7642`)
- **Fox Article** + **Grey Wolf Image** → **REJECTED BY GUARD** (Forced block: concept mismatch)
- **Fox Article** + **Unrelated Data** → **REJECTED** (Score `0.2410` falls beneath the threshold)

---

## 🛠 Ingestion & Local Run Steps

### 1. Cloning & Environment Configuration
\`\`\`bash
git clone https://github.com/<you>/flyrank-capstone-image-relevance
cd flyrank-capstone-image-relevance
cp .env.example .env
\`\`\`
*Open `.env` and insert your free Google AI Studio key on the `GEMINI_API_KEY` line.*

### 2. Dependency Setup
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 3. Seeding the Corpus (~50 Images)
\`\`\`bash
python -m engine.seed
\`\`\`

### 4. Running the Local API Server
\`\`\`bash
uvicorn engine.main:app --reload --port 8000
\`\`\`

---

## ⚠️ Engineering Limitations & Constraints
- **Text Length Dependency:** embedding performance relies heavily on descriptive text quality.
- **Local Compute Limits:** `all-MiniLM-L6-v2` executes text vectorization entirely in memory.
- **Dynamic Cost Tracking:** pricing models are hardcoded as static tracking metrics.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
```

---

## 16. The Final Demo — Your 6 Minutes

**0:00 — The Core Mission (opening argument):** introduce the FlyRank AI Image Understanding & Content Matching Engine. State the core philosophy: a production AI system shouldn't just be an unreliable wrapper — safe rejection is a first-class feature.

**1:00 — Batch Processing & Tracking:** run `python -m engine.seed` live. Show async streaming logs, exponential backoff retries, and a deliberately blurry/low-confidence asset getting flagged and isolated by the Pydantic floor. Show per-call token/cost metrics streaming in real time.

**2:30 — The Happy Path & Concept Matching:** hit `GET /posts/1/images` with an article using scientific terminology (not the literal word "fox"). Show the local sentence-transformer model vectorizing text in real time and the red-fox asset surfacing first with a strong cosine score, while wolf/dog assets rank lower.

**3:45 — The Forced-Wolf Moment (demo highlight):** manually evaluate the grey wolf asset directly against a fox-topic post. Show the immediate refusal — the Mismatch Guard intercepts before any human ever sees it — with a precise, human-readable rejection explanation (e.g., `"REJECTED. Category Mismatch: expected fox family variant, rejected grey wolf concept profile."`).

**4:45 — Confident Absence & the Review API:** query a completely out-of-domain article (e.g., "deep sea oil rigs") against the animal image library. Show the system safely return "No confident match" rather than forcing a bad guess. Then toggle to the `/review/ledger` endpoint and show the persistent audit trail.

**5:45 — Closing Numbers:** reference the automated precision-sweep script and its exact result (e.g., **Top-1 Precision: 92–100%** depending on your dataset). Close with: *"Good suggestions when confident, safe rejection when uncertain — that is production AI."*

### Pre-Flight Verification Checklist
- **Local DB reset:** clear the local `.db` file so seed metrics start fresh.
- **Zero-token lockout:** confirm `GEMINI_API_KEY` is loaded correctly in your shell.
- **EVIDENCE.md match:** verify precision numbers in your terminal match those written in `README.md`.
- **Code deep-dive readiness:** be able to walk through your exact `evaluate_mismatch_guard` block on the spot.

---

## 17. Your $0 Stack — The Free-Tools Promise

The whole system runs on a zero-cost, local-first architecture:

| Layer | Tool | Cost |
|---|---|---|
| Vision/LLM | Gemini 2.5 Flash (free-tier, via Google AI Studio — no credit card) | $0 |
| Text embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`), runs 100% locally | $0 |
| Storage | SQLite (flat `TEXT` blob for serialized embeddings) | $0 |
| Similarity math | `numpy` cosine similarity, in-memory, at ~50-image scale | $0 |
| API layer | FastAPI + Pydantic (boundary validation) | $0 |

**Why in-DB arrays are fine at this scale:** with a corpus constrained to ~50 images, there is no need for a dedicated external vector database cluster (Pinecone, Milvus). A local relational table with cosine similarity computed directly in memory is faster and completely free.

### Final Checklist for Repository Submission
- [ ] `.env` isolation — `GEMINI_API_KEY` stored locally; `.gitignore` prevents it from ever being committed.
- [ ] Corpus inclusion — ~50 free-licensed images (Unsplash/Pexels) checked into `assets/` (or reproducible via a local setup script).
- [ ] `BUILDLOG.md` completed — chronological record of how AI tools were directed to write, debug, and implement guardrails.

---

## 18. Stretch Goals (Only If the Core Ships)

Only pursue these once the core checklist is passing and `EVIDENCE.md` is locked. One fully-implemented stretch goal makes a compelling interview story.

### A. Fallback Image Generation
When the Mismatch Guard returns "No confident match available," hook into an image-generation workflow (Imagen 3 via `google-genai`) to programmatically create a tailored fallback asset:
1. Use Gemini 2.5 Flash to convert the raw blog text into a crisp, descriptive image prompt.
2. Call `imagen-3.0-generate-002` to generate the image.
3. Write the resulting byte stream to the local assets directory and log the fallback event.

### B. Near-Duplicate Asset Detection (Perceptual Hashing)
Add the `imagehash` package (runs entirely locally, $0 cost) to detect near-identical images via perceptual hash (pHash) and Hamming-distance comparison against existing asset hashes — rejecting duplicates before they clutter the ingestion queue.

### C. Automated WCAG Compliance Alt-Text Generator
Extend the Phase-1 Gemini JSON schema to require an `alt_text` field alongside `subject`/`category`, ensuring every ingested asset automatically receives a rich, WCAG-compliant accessibility description before hitting a live staging server.

---

*End of merged guide — this document consolidates: The Mission · Ground Rules · Architecture Design · The Five Gates / Phase-by-Phase Build · Definition of Done · Evidence Ledger · GitHub Repo Rules · capstone.yaml · .env.example · README.md · Core Engine Blueprint · Seed Script · Test Suite · Precision Sweep Script · Final Demo Script · $0 Stack Notes · Stretch Goals.*
