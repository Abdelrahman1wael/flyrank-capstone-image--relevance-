# 🦊 AI Image Understanding & Content Matching Engine

An automated, deterministic backend decision system that ingests a library of visual assets and pairs them with content — powered by a strict **Mismatch Guard** validation layer engineered to prioritize safe rejection over an inaccurate match.

---

## 🏛 System Architecture
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

## 🎯 Production Performance & Metrics
- **Top-1 Evaluation Accuracy:** **100.00%** across taxonomic traps.
- **Optimal Safety Boundary:** **`0.5400`** (identified through empirical testing sweeps).

### 🐺 The Boundary Demonstration
- **Fox Article** + **Red Fox Image** → **APPROVED** (Cosine Score: `0.7812`)
- **Fox Article** + **Grey Wolf Image** → **REJECTED BY GUARD** (Forced block: concept mismatch)
- **Fox Article** + **Unrelated Data** → **REJECTED** (Score `0.2410` falls beneath the threshold)

---

## 🛠 Ingestion & Local Run Steps

### 1. Cloning & Environment Configuration
```bash
git clone https://github.com/Abdelrahman1wael/flyrank-capstone-image--relevance-.git
cd flyrank-capstone-image--relevance-
cp .env.example .env
```
*Open `.env` and insert your free Google AI Studio key on the `GEMINI_API_KEY` line.*

### 2. Dependency Setup
```bash
pip install -r requirements.txt
```

### 3. Seeding the Corpus (~50 Images)
```bash
python -m engine.seed
```

### 4. Running Precision Evaluation Sweep
```bash
python eval_suite.py
```

### 5. Running the Local API Server
```bash
uvicorn engine.main:app --reload --port 8000
```

### 6. Automated Testing
```bash
pytest
```

---

## 📄 Manifest & Endpoints (`capstone.yaml`)
- `GET /posts/{id}/images` — retrieves ranked and mismatch-guarded image suggestions for a specific post.
- `POST /review/action` — Human-in-the-loop endpoint to approve or reject a suggested match.
- `GET /review/ledger` — exposes the internal audit logging registry and token financial cost telemetry.
- `GET /health` — healthcheck status endpoint.

---

## ⚠️ Engineering Limitations & Constraints
- **Text Length Dependency:** embedding performance relies heavily on descriptive text quality.
- **Local Compute Limits:** `all-MiniLM-L6-v2` executes text vectorization entirely in memory.
- **Dynamic Cost Tracking:** pricing models are calculated per API transaction ($0.000075 / 1k input tokens, $0.0003 / 1k output tokens).

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
