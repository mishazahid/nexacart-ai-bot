#!/bin/bash
set -e

echo "Running ingestion pipeline..."
python -c "
from src.ingestion.pipeline import run_ingestion
from src.retrieval.bm25_search import load_bm25_index
from src.retrieval.vector_search import load_vector_index
result = run_ingestion()
print(f'Ingestion complete: {result}')
"

echo "Starting server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
