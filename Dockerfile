FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system and Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download SentenceTransformer model during build to ensure instant runtime startup
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application files
COPY engine/ /app/engine/
COPY eval_suite.py /app/
COPY capstone.yaml /app/
COPY .env.example /app/

# Expose FastAPI server port
EXPOSE 8000

# Launch Uvicorn server
CMD ["uvicorn", "engine.main:app", "--host", "0.0.0.0", "--port", "8000"]
