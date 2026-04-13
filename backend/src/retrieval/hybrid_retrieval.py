"""
NexaCart AI Support Bot - Hybrid Retrieval

Combines BM25 keyword search and FAISS vector search using a weighted
score fusion formula:

    final_score = 0.45 * bm25_score + 0.55 * vector_score

Chunks present in only one result set are assigned a score of 0 for the
missing component.
"""
from typing import Dict, List, Tuple

from app.config import settings
from app.logger import get_logger
from src.retrieval.bm25_search import bm25_search
from src.retrieval.vector_search import vector_search

logger = get_logger(__name__)


def hybrid_search(query: str, top_k: int = 5) -> List[Dict]:
    """
    Execute a hybrid BM25 + vector search and fuse results by weighted score.

    The retrieval strategy:
    1. Fetch ``top_k * 2`` results from BM25.
    2. Fetch ``top_k * 2`` results from vector search.
    3. Build a union of all unique chunks (keyed by ``(filename, chunk_index)``).
    4. Compute ``final_score = 0.45 * bm25_score + 0.55 * vector_score`` for
       each chunk (missing scores default to 0).
    5. Sort by ``final_score`` descending and return the top ``top_k`` results.

    Args:
        query: The user's natural-language query string.
        top_k: Number of final results to return.

    Returns:
        List of fused result dicts sorted by ``final_score`` descending, each
        containing:
        - ``chunk_text``
        - ``filename``
        - ``chunk_index``
        - ``final_score`` (0–1)
        - ``bm25_score`` (0–1, 0 if not in BM25 results)
        - ``vector_score`` (0–1, 0 if not in vector results)
    """
    candidate_k = top_k * 2

    bm25_results = bm25_search(query, top_k=candidate_k)
    vector_results = vector_search(query, top_k=candidate_k)

    # Key: (filename, chunk_index) -> merged score dict
    merged: Dict[Tuple[str, int], Dict] = {}

    for item in bm25_results:
        key: Tuple[str, int] = (item["filename"], item["chunk_index"])
        merged[key] = {
            "chunk_text": item["chunk_text"],
            "filename": item["filename"],
            "chunk_index": item["chunk_index"],
            "bm25_score": item["bm25_score"],
            "vector_score": 0.0,
        }

    for item in vector_results:
        key = (item["filename"], item["chunk_index"])
        if key in merged:
            merged[key]["vector_score"] = item["vector_score"]
        else:
            merged[key] = {
                "chunk_text": item["chunk_text"],
                "filename": item["filename"],
                "chunk_index": item["chunk_index"],
                "bm25_score": 0.0,
                "vector_score": item["vector_score"],
            }

    # Compute weighted final score
    fused: List[Dict] = []
    for entry in merged.values():
        final_score = (
            settings.BM25_WEIGHT * entry["bm25_score"]
            + settings.VECTOR_WEIGHT * entry["vector_score"]
        )
        fused.append(
            {
                "chunk_text": entry["chunk_text"],
                "filename": entry["filename"],
                "chunk_index": entry["chunk_index"],
                "final_score": round(final_score, 6),
                "bm25_score": round(entry["bm25_score"], 6),
                "vector_score": round(entry["vector_score"], 6),
            }
        )

    fused.sort(key=lambda x: x["final_score"], reverse=True)
    top_results = fused[:top_k]

    logger.debug(
        "Hybrid search for %r: %d BM25, %d vector, %d merged → top %d returned.",
        query,
        len(bm25_results),
        len(vector_results),
        len(fused),
        len(top_results),
    )
    return top_results
