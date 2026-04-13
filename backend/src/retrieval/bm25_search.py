"""
NexaCart AI Support Bot - BM25 Search

Loads the BM25Okapi index from disk and provides keyword-based retrieval
with min-max normalised scores.
"""
import pickle
from typing import Dict, List, Optional, Tuple

import numpy as np
from rank_bm25 import BM25Okapi

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# Module-level cache so we only load from disk once
_bm25_index: Optional[BM25Okapi] = None
_corpus: Optional[List[Dict]] = None


def load_bm25_index() -> None:
    """
    Load the BM25 index and corpus metadata from disk into module-level cache.

    Must be called before :func:`bm25_search` is invoked.  Safe to call
    multiple times — subsequent calls are no-ops.
    """
    global _bm25_index, _corpus
    if _bm25_index is not None:
        return  # Already loaded

    try:
        with open(settings.BM25_INDEX_PATH, "rb") as fh:
            data = pickle.load(fh)
        _bm25_index = data["bm25"]
        _corpus = data["corpus"]
        logger.info(
            "BM25 index loaded from %s (%d documents in corpus)",
            settings.BM25_INDEX_PATH,
            len(_corpus),
        )
    except FileNotFoundError:
        logger.error(
            "BM25 index file not found at %s. Run the ingestion pipeline first.",
            settings.BM25_INDEX_PATH,
        )
        raise


def bm25_search(query: str, top_k: int = 5) -> List[Dict]:
    """
    Retrieve the top-k most relevant chunks using BM25 keyword scoring.

    Scores are min-max normalised to the range [0, 1].  If all raw scores are
    zero (no term overlap), every chunk receives a normalised score of 0.0 and
    the first ``top_k`` chunks are returned.

    Args:
        query: The user's natural-language query string.
        top_k: Maximum number of results to return.

    Returns:
        List of result dicts sorted by ``bm25_score`` descending, each with:
        - ``chunk_text``
        - ``filename``
        - ``chunk_index``
        - ``bm25_score`` (normalised, 0–1)
        - ``raw_score`` (original BM25 score)
    """
    if _bm25_index is None or _corpus is None:
        load_bm25_index()

    tokenized_query: List[str] = query.lower().split()
    raw_scores: np.ndarray = np.array(_bm25_index.get_scores(tokenized_query))  # type: ignore[union-attr]

    score_min = float(raw_scores.min())
    score_max = float(raw_scores.max())

    if score_max - score_min < 1e-9:
        # All scores identical (typically all zero) — normalise to 0
        normalised = np.zeros_like(raw_scores)
    else:
        normalised = (raw_scores - score_min) / (score_max - score_min)

    # Get indices sorted by score descending
    top_indices: List[int] = list(
        np.argsort(normalised)[::-1][:top_k]
    )

    results: List[Dict] = []
    for idx in top_indices:
        chunk = _corpus[idx]  # type: ignore[index]
        results.append(
            {
                "chunk_text": chunk["chunk_text"],
                "filename": chunk["filename"],
                "chunk_index": chunk["chunk_index"],
                "bm25_score": round(float(normalised[idx]), 6),
                "raw_score": round(float(raw_scores[idx]), 6),
            }
        )

    logger.debug("BM25 search for %r returned %d results.", query, len(results))
    return results
