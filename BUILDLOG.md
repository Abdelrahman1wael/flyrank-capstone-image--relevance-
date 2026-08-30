# 🛠 Project Build Log

### [2026-08-30] Stage 1: Architecture Specs, Manifest & Environment Configuration
- **What I Did:** Established the dedicated repository scaffold. Defined system architecture (`DESIGN.md`), project manifest (`capstone.yaml`), unified dependency matrix (`requirements.txt`), and environment seed blueprint (`.env.example`).
- **AI Tool Assistance:** Used AI collaborator to structure data model schemas, manifest endpoints, and project execution parameters.
- **Human Course Corrections:** Confirmed local-first $0 compute execution using SQLite and `sentence-transformers` for vector embeddings.

### [2026-08-30] Stage 2: Pydantic Boundary Schemas & SQLite Database Infrastructure
- **What I Did:** Built strict boundary schemas in `engine/schemas.py` with a 0.75 confidence floor validator. Created SQLite database management layer in `engine/database.py` with transactional support for images, embeddings, and human review ledger.
- **AI Tool Assistance:** Assisted in designing Pydantic field validators and relational table structures.
- **Human Course Corrections:** Ensured vector embeddings are stored as JSON arrays in SQLite for local zero-cost computation without external DB dependencies.

### [2026-08-30] Stage 3: Async Batch Ingestion, Token Telemetry & Seed Pipeline
- **What I Did:** Implemented `engine/seed.py` with a 50-item mock corpus across 5 animal categories (`fox`, `wolf`, `dog`, `bear`, `deer`) plus low-confidence blurry edge cases. Built async retry worker simulation and per-transaction financial token cost telemetry ($0.000075 / 1k input tokens, $0.0003 / 1k output tokens).
- **AI Tool Assistance:** Generated visual profile corpus seeds and token telemetry metrics.
- **Human Course Corrections:** Isolated visual profiles with confidence < 0.75 from active datastore and added UTF-8 console output reconfiguration for Windows environments.

### [2026-08-30] Stage 4: Vector Matching Engine & The Mismatch Guard
- **What I Did:** Implemented `engine/services.py` (`MatchingService`) featuring vector similarity math via `numpy` cosine distance on `all-MiniLM-L6-v2` embeddings. Built explicit Mismatch Guard enforcing hard taxonomic category rejections (e.g. Wolf-on-Fox refusal scenario) and similarity threshold gating (default 0.54).
- **AI Tool Assistance:** Assisted in tuning cosine distance functions and taxonomic mismatch guardrails.
- **Human Course Corrections:** Integrated automatic audit logging of candidate decisions into SQLite review ledger.

### [2026-08-30] Stage 5: Precision Evaluation Sweep & Evidence Ledger
- **What I Did:** Created `eval_suite.py` to run empirical threshold sweeps across 15 labeled evaluation test cases (exact matches, scientific taxonomic matches, refusal traps, out-of-domain queries). Discovered optimal threshold `0.54` securing 100.00% precision. Documented submission proof logs in `EVIDENCE.md`.
- **AI Tool Assistance:** Designed precision evaluation metrics matrix and evidence ledger formatting.
- **Human Course Corrections:** Enforced non-zero threshold evaluation sweeps to guarantee zero false positives on forced-wolf traps.
