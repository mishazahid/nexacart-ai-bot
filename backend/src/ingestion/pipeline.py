"""
NexaCart AI Support Bot - Ingestion Pipeline

Orchestrates document loading, chunking, embedding generation, FAISS index
construction, BM25 index construction, and database persistence.

Run directly:
    python src/ingestion/pipeline.py
"""
import os
import pickle
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List

# Allow running as __main__ from the backend/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, create_tables
from app.logger import get_logger
from app.models import DocumentChunk
from src.ingestion.chunker import chunk_all_documents
from src.ingestion.loader import load_documents

logger = get_logger(__name__)


def _ensure_dirs() -> None:
    """Create required data directories if they do not already exist."""
    for path in [
        os.path.dirname(settings.FAISS_INDEX_PATH),
        os.path.dirname(settings.CHUNKS_METADATA_PATH),
        os.path.dirname(settings.BM25_INDEX_PATH),
        os.path.dirname(settings.LOG_PATH),
    ]:
        if path:
            os.makedirs(path, exist_ok=True)


def _generate_embeddings(
    chunks: List[Dict], model: SentenceTransformer, batch_size: int = 64
) -> np.ndarray:
    """
    Generate L2-normalised sentence embeddings for all chunks.

    Args:
        chunks: List of chunk dicts (must contain ``chunk_text`` key).
        model: Loaded SentenceTransformer model.
        batch_size: Number of texts to embed per forward pass.

    Returns:
        Float32 numpy array of shape (len(chunks), embedding_dim).
    """
    texts: List[str] = [c["chunk_text"] for c in chunks]
    logger.info("Generating embeddings for %d chunks (batch_size=%d)…", len(texts), batch_size)
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return embeddings.astype(np.float32)


def _save_chunks_to_db(chunks: List[Dict], db: Session) -> None:
    """Persist all chunk metadata to the SQLite database."""
    # Clear existing records to allow re-ingestion
    db.query(DocumentChunk).delete()
    db.commit()

    records: List[DocumentChunk] = [
        DocumentChunk(
            id=str(uuid.uuid4()),
            filename=c["filename"],
            chunk_index=c["chunk_index"],
            content=c["chunk_text"],
            word_count=c["word_count"],
            created_at=datetime.utcnow(),
        )
        for c in chunks
    ]
    db.bulk_save_objects(records)
    db.commit()
    logger.info("Saved %d DocumentChunk records to database.", len(records))


def run_ingestion() -> Dict:
    """
    Execute the full ingestion pipeline.

    Steps:
        1. Load Markdown documents from the knowledge base directory.
        2. Chunk documents with sliding-window word-based chunking.
        3. Generate sentence embeddings in batches.
        4. Build a FAISS IndexFlatL2 and persist it.
        5. Build a BM25Okapi index and persist it alongside the corpus.
        6. Persist chunk metadata via pickle and to the SQLite database.

    Returns:
        A summary dict with keys:
        ``status``, ``total_docs``, ``total_chunks``, ``time_taken_seconds``.
    """
    start_time = time.time()
    logger.info("=== Starting NexaCart knowledge base ingestion ===")

    _ensure_dirs()
    create_tables()

    # Step 1 – Load documents
    documents = load_documents(settings.KNOWLEDGE_BASE_PATH)
    if not documents:
        raise RuntimeError("No documents found in knowledge base. Aborting ingestion.")

    # Step 2 – Chunk
    chunks = chunk_all_documents(
        documents,
        chunk_size=settings.CHUNK_SIZE,
        overlap=settings.CHUNK_OVERLAP,
    )
    if not chunks:
        raise RuntimeError("No chunks generated from documents. Aborting ingestion.")

    # Step 3 – Embeddings
    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    embeddings = _generate_embeddings(chunks, model)

    # Step 4 – FAISS index
    dim: int = embeddings.shape[1]
    faiss_index = faiss.IndexFlatL2(dim)
    faiss_index.add(embeddings)
    faiss.write_index(faiss_index, settings.FAISS_INDEX_PATH)
    logger.info(
        "FAISS index saved to %s (%d vectors, dim=%d)",
        settings.FAISS_INDEX_PATH,
        faiss_index.ntotal,
        dim,
    )

    # Step 5 – BM25 index
    tokenized_corpus: List[List[str]] = [
        c["chunk_text"].lower().split() for c in chunks
    ]
    bm25_index = BM25Okapi(tokenized_corpus)
    with open(settings.BM25_INDEX_PATH, "wb") as fh:
        pickle.dump({"bm25": bm25_index, "corpus": chunks}, fh)
    logger.info("BM25 index saved to %s", settings.BM25_INDEX_PATH)

    # Step 6 – Chunks metadata pickle
    with open(settings.CHUNKS_METADATA_PATH, "wb") as fh:
        pickle.dump(chunks, fh)
    logger.info("Chunk metadata saved to %s", settings.CHUNKS_METADATA_PATH)

    # Step 7 – Database persistence
    db: Session = SessionLocal()
    try:
        _save_chunks_to_db(chunks, db)
    finally:
        db.close()

    elapsed = round(time.time() - start_time, 2)
    result = {
        "status": "success",
        "total_docs": len(documents),
        "total_chunks": len(chunks),
        "time_taken_seconds": elapsed,
    }
    logger.info("=== Ingestion complete: %s ===", result)
    return result


if __name__ == "__main__":
    summary = run_ingestion()
    print("\nIngestion Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
