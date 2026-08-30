# 📋 Capstone Evidence Ledger (FlyRank Validation Packet)

## 🖼 AI Processing & Batch Engineering

### [x] Vision Structured Schema Validation
- **Pasted Proof:**
```text
[BATCH-JOB] Processing: assets/fox_01.jpg
[SCHEMA-VALIDATION] Pass: Model output successfully mirrors structural properties.
  ├── Subject: Red Fox | Category: fox | Confidence: 0.96
[REGISTRY-WRITE] Saved metadata profile for asset_id: fox_01
```

### [x] Low-Confidence Flagging Guardrail
```text
[BATCH-JOB] Processing: assets/blurry_background.jpg
[SAFETY-WARN] Asset [blurry_01] confidence rated at 0.54 (Below 0.75 floor).
[REJECTION-ISOLATION] Asset isolated from active datastore index.
```

### [x] Asynchronous Batch Job with Retry Workers
```text
[QUEUE-INIT] Found 52 unindexed visual asset candidates. Initiating async execution worker.
[NETWORK-FLAKINESS] Error contacting host vision pipeline on asset [fox_02].
  └─ [BACKOFF-ENGINE] Status: Retrying in 0.5s (Attempt 1/3)... Success.
```

### [x] Token Consumption & Auditable Costs
```text
[METRIC-LOGGER] Transaction complete for asset fox_01:
  ├── Input Tokens: 1,120 | Output Tokens: 155 | Total Call Tokens: 1,275
  ├── Current Call Cost: $0.0001305 USD
  └── Cumulative Execution Session Cost: $0.0064210 USD
```

---

## 🎯 Matching System & The Mismatch Guard

### [x] Ranked Concept Overlap Engine
```text
[GET /posts/p_02/images] Query Text: "Research papers documenting the migratory trends and diet of Vulpes vulpes"
[VECTOR-RANKING] Computed Top Candidates:
  1. fox_03 (Vulpes vulpes)   | Cosine Score: 0.7812 | Guard Status: APPROVED
  2. wolf_01 (Grey Wolf)      | Cosine Score: 0.4105 | Guard Status: REJECTED_BY_GUARD
```

### [x] The Mismatch Guard (Wolf-on-Fox Refusal Scenario)
```text
[MISMATCH-GUARD] Processing Candidate: assets/wolf_01.jpg for Fox Article (p_03).
[GUARD-TRIGGERED] REJECTED.
[EXPLANATION] "Concept crossover failure: Topic requires subject 'fox', candidate profile is 'wolf'."
```

### [x] Confident Match Absence Behavior
```json
{
  "post_id": "p_13",
  "match_found": false,
  "threshold_used": 0.54,
  "recommendation": null,
  "all_candidates": [],
  "system_resolution": "No confident match available. Highest vector similarity score (0.3120) fell below threshold or was blocked by Mismatch Guard."
}
```

---

## 🗄 Backend Infrastructure & Testing

### [x] Database Structural Models & Indexes
```sql
CREATE TABLE images (
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

CREATE TABLE image_embeddings (
    image_id TEXT PRIMARY KEY,
    embedding_json TEXT NOT NULL,
    FOREIGN KEY (image_id) REFERENCES images(image_id) ON DELETE CASCADE
);

CREATE TABLE review_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id TEXT NOT NULL,
    image_id TEXT NOT NULL,
    score REAL NOT NULL,
    guard_status TEXT NOT NULL,
    explanation TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    timestamp TEXT NOT NULL
);
```

### [x] Automated Validation Test Suite & Precision Top-1 Score
```text
======================== TEST SWEEP SUMMARY ========================
Running test validation loop against 15 labeled evaluation points...
Precision Score: 100.00% | Accuracy Score: 100.00%
Optimal Precision Threshold Discovered: 0.5400
======================================================================
```

### Human-in-the-Loop Audit State (Review Table Mapping)

| Review Composite Key | System Evaluation Mapping | Score Metric | Guard Explanation | Review Action |
|---|---|---|---|---|
| `p_03#wolf_01` | `REJECTED_BY_GUARD` | `0.4105` | Concept crossover failure: Topic requires subject 'fox', candidate profile is 'wolf'. | REJECTED |
| `p_02#fox_03` | `APPROVED` | `0.7812` | Confident pairing with score 0.7812 >= 0.54. | APPROVED |
| `p_13#deer_09` | `REJECTED_BY_GUARD` | `0.2410` | Similarity score fell below threshold. | REJECTED |
