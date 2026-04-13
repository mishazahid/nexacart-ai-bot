"""
NexaCart AI Support Bot - Vector Search

Loads the FAISS index and chunk metadata from disk and provides dense
vector-based semantic retrieval.
"""
import pickle
from typing import Dict, List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# Module-level cache
_faiss_index: Optional[faiss.Index] = None
_chunks_metadata: Optional[List[Dict]] = None
_embedding_model: Optional[SentenceTransformer] = None


def load_vector_index() -> None:
    """
    Load the FAISS index, chunk metadata, and sentence-transformer model into
    the module-level cache.

    Safe to call multiple times — subsequent calls are no-ops.
    """
    global _faiss_index, _chunks_metadata, _embedding_model
    if _faiss_index is not None:
        return  # Already loaded

    try:
        _faiss_index = faiss.read_index(settings.FAISS_INDEX_PATH)
        logger.info(
            "FAISS index loaded from %s (%d vectors)",
            settings.FAISS_INDEX_PATH,
            _faiss_index.ntotal,
        )
    except Exception as exc:
        logger.error("Failed to load FAISS index: %s", exc)
        raise

    try:
        with open(settings.CHUNKS_METADATA_PATH, "rb") as fh:
            _chunks_metadata = pickle.load(fh)
        logger.info(
            "Chunk metadata loaded from %s (%d chunks)",
            settings.CHUNKS_METADATA_PATH,
            len(_chunks_metadata),
        )
    except FileNotFoundError:
        logger.error(
            "Chunk metadata file not found at %s. Run the ingestion pipeline first.",
            settings.CHUNKS_METADATA_PATH,
        )
        raise

    _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    logger.info("Sentence-transformer model loaded: %s", settings.EMBEDDING_MODEL)


def vector_search(query: str, top_k: int = 5) -> List[Dict]:
    """
    Retrieve the top-k most semantically similar chunks using FAISS.

    L2 distances are converted to a similarity score via:
    ``score = 1 / (1 + distance)``
    so that closer vectors (smaller distance) yield higher scores.

    Args:
        query: The user's natural-language query string.
        top_k: Maximum number of results to return.

    Returns:
        List of result dicts sorted by ``vector_score`` descending, each with:
        - ``chunk_text``
        - ``filename``
        - ``chunk_index``
        - ``vector_score`` (0–1, higher is better)
        - ``distance`` (raw L2 distance)
    """
    if _faiss_index is None or _chunks_metadata is None or _embedding_model is None:
        load_vector_index()

    query_embedding: np.ndarray = _embedding_model.encode(  # type: ignore[union-attr]
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    distances, indices = _faiss_index.search(query_embedding, top_k)  # type: ignore[union-attr]

    results: List[Dict] = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(_chunks_metadata):  # type: ignore[arg-type]
            continue
        chunk = _chunks_metadata[idx]  # type: ignore[index]
        similarity_score = 1.0 / (1.0 + float(dist))
        results.append(
            {
                "chunk_text": chunk["chunk_text"],
                "filename": chunk["filename"],
                "chunk_index": chunk["chunk_index"],
                "vector_score": round(similarity_score, 6),
                "distance": round(float(dist), 6),
            }
        )

    logger.debug("Vector search for %r returned %d results.", query, len(results))
    return results
