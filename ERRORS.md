# Errors & Troubleshooting Guide

This guide documents common operational, runtime, environment, and container errors encountered in the **AI Image Understanding & Content Matching Engine**, along with root cause analysis and resolution steps.

---

## 1. Docker & Container Errors

### 1.1 Container Name Conflict
* **Error**: `Error response from daemon: Conflict. The container name "/flyrank_matching_engine" is already in use`
* **Root Cause**: An existing container with the specified name is already running or stopped in Docker.
* **Resolution**:
  - **PowerShell**:
    ```powershell
    docker compose down; docker compose up -d
    ```
  - **Bash / Command Prompt**:
    ```bash
    docker compose down && docker compose up -d
    ```

---

### 1.2 Docker Build Timeout / Heavy PyTorch Downloads
* **Error**: `pip install -r requirements.txt` hangs for >10 minutes or fails with `ReadTimeoutError`.
* **Root Cause**: Installing `sentence-transformers` without specifying PyTorch CPU wheels forces `pip` to download ~2.5 GB of GPU CUDA binaries from standard PyPI.
* **Resolution**: Ensure [`Dockerfile`](file:///c:/Users/hp/Desktop/capstone-image-relevance/Dockerfile) includes the PyTorch CPU index URL prior to `requirements.txt`:
  ```dockerfile
  RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu
  RUN pip install --no-cache-dir -r requirements.txt
  ```

---

### 1.3 Port 8000 Binding Conflict
* **Error**: `listen tcp 0.0.0.0:8000: bind: An attempt was made to access a socket in a way forbidden by its access permissions` or `address already in use`.
* **Root Cause**: Another process (e.g. local Uvicorn instance, another server) is bound to port `8000`.
* **Resolution**:
  - Locate the PID using port `8000`:
    ```powershell
    netstat -ano | findstr :8000
    ```
  - Stop the process:
    ```powershell
    taskkill /PID <PID> /F
    ```

---

### 1.4 Invalid PowerShell Statement Separator (`&&`)
* **Error**: `The token '&&' is not a valid statement separator in this version.`
* **Root Cause**: Windows PowerShell v5.1 does not support `&&` chaining.
* **Resolution**: Use `;` as the command separator in PowerShell:
  ```powershell
  docker compose down; docker compose up -d
  ```

---

## 2. Machine Learning & Embedding Model Errors

### 2.1 Hugging Face Hub Rate Limit Warning / Slow First Load
* **Error**: `Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits...`
* **Root Cause**: Anonymous model retrieval requests sent to Hugging Face Hub during `SentenceTransformer` instantiation.
* **Resolution**:
  - Model weights are pre-cached into the image during Docker build step:
    ```dockerfile
    RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
    ```
  - Optionally define `HF_TOKEN` in your `.env` file to bypass anonymous rate limits.

---

### 2.2 Mismatch Guard Over-Filtering (Empty Candidates)
* **Error**: Endpoint `/posts/{id}/images` returns `candidates: []` with `guard_triggered: true` for relevant posts.
* **Root Cause**: `MISMATCH_GUARD_THRESHOLD` is set too high (e.g. `>0.70`), causing valid candidate embeddings to fall below threshold.
* **Resolution**:
  - Set `MISMATCH_GUARD_THRESHOLD=0.54` (recommended baseline) in your `.env` or `docker-compose.yml` environment block.

---

## 3. Database & Persistence Errors

### 3.1 Missing Tables (`sqlite3.OperationalError: no such table: images`)
* **Error**: API requests or seed scripts fail with `sqlite3.OperationalError: no such table: images`.
* **Root Cause**: SQLite database has not been initialized with required schema tables.
* **Resolution**:
  - Run the database seed script to populate tables:
    ```bash
    python -m engine.seed
    ```
  - Alternatively, restart the FastAPI app; the `lifespan` handler executes `init_db()` automatically on startup.

---

### 3.2 Database Lock Errors (`sqlite3.OperationalError: database is locked`)
* **Error**: Concurrent API requests or review audits trigger database locked exceptions.
* **Root Cause**: SQLite default journal mode blocking concurrent write transactions.
* **Resolution**:
  - Ensure connections use short-lived context managers via `get_db_connection()`.
  - Re-run database seed or verify `flyrank_cms.db` file permissions.

---

## 4. API & External Service Errors

### 4.1 Gemini API Key Missing
* **Error**: `google.genai.errors.APIError` or `ValueError: GEMINI_API_KEY environment variable not set`.
* **Root Cause**: Multi-modal vision analysis feature requires a valid Google Gemini API key.
* **Resolution**:
  - Create a `.env` file based on `.env.example`:
    ```env
    GEMINI_API_KEY=your_actual_api_key_here
    DATABASE_URL=sqlite:///flyrank_cms.db
    MISMATCH_GUARD_THRESHOLD=0.54
    ```

---

### 4.2 Endpoint Health / 404 Not Found
* **Error**: `GET /posts/p_invalid/images` returns empty matches or error payload.
* **Root Cause**: Target Post ID is not in `SAMPLE_POSTS` and query text was omitted.
* **Resolution**: Pass an explicit `query` override query parameter:
  ```http
  GET /posts/p_invalid/images?query=wildlife+and+fox+behavior
  ```

---

## Quick Reference Summary Table

| Category | Typical Exception / Message | Primary Workaround |
| :--- | :--- | :--- |
| **Docker** | Container name `/flyrank_matching_engine` in use | Run `docker compose down; docker compose up -d` |
| **Docker** | PyTorch download time > 10m | Use `--extra-index-url https://download.pytorch.org/whl/cpu` |
| **Shell** | `'&&'` is not a valid statement separator | Use `;` instead of `&&` in PowerShell |
| **Model** | Unauthenticated HF Hub requests warning | Model pre-cached in Dockerfile; add `HF_TOKEN` if needed |
| **Database** | `no such table: images` | Run `python -m engine.seed` or restart app |
| **API** | `candidates: []` on valid query | Adjust `MISMATCH_GUARD_THRESHOLD` to `0.54` |
