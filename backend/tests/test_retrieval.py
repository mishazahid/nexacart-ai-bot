"""
Tests for BM25, vector, and hybrid retrieval modules.

These tests assume the ingestion pipeline has already been run and the
index files are present on disk.  Run ``python src/ingestion/pipeline.py``
before executing this test suite.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from src.retrieval.bm25_search import bm25_search, load_bm25_index
from src.retrieval.hybrid_retrieval import hybrid_search
from src.retrieval.vector_search import load_vector_index, vector_search


# ---------------------------------------------------------------------------
# Fixtures — load indexes once per session
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def load_indexes():
    """Load BM25 and vector indexes before any retrieval tests run."""
    load_bm25_index()
    load_vector_index()


# ---------------------------------------------------------------------------
# BM25 tests
# ---------------------------------------------------------------------------


def test_bm25_returns_results():
    """A shipping query should return at least one BM25 result."""
    results = bm25_search("How long does shipping take?", top_k=5)
    assert len(results) > 0, "BM25 returned no results for a shipping query"


def test_bm25_result_structure():
    """Each BM25 result should contain the required keys."""
    results = bm25_search("return policy", top_k=3)
    for r in results:
        assert "chunk_text" in r
        assert "filename" in r
        assert "chunk_index" in r
        assert "bm25_score" in r
        assert "raw_score" in r


def test_bm25_scores_normalised():
    """All BM25 scores should be in the range [0, 1]."""
    results = bm25_search("payment methods accepted", top_k=5)
    for r in results:
        assert 0.0 <= r["bm25_score"] <= 1.0, (
            f"BM25 score out of range: {r['bm25_score']}"
        )


# ---------------------------------------------------------------------------
# Vector search tests
# ---------------------------------------------------------------------------


def test_vector_returns_results():
    """A return policy query should return at least one vector result."""
    results = vector_search("return policy refund", top_k=5)
    assert len(results) > 0, "Vector search returned no results"


def test_vector_result_structure():
    """Each vector result should contain the required keys."""
    results = vector_search("how do I reset my password", top_k=3)
    for r in results:
        assert "chunk_text" in r
        assert "filename" in r
        assert "chunk_index" in r
        assert "vector_score" in r
        assert "distance" in r


def test_vector_scores_in_range():
    """All vector scores should be positive (L2 distance → similarity conversion)."""
    results = vector_search("exchange shipping free", top_k=5)
    for r in results:
        assert r["vector_score"] > 0.0, (
            f"Vector score should be positive, got {r['vector_score']}"
        )
        assert r["vector_score"] <= 1.0, (
            f"Vector score should be ≤ 1.0, got {r['vector_score']}"
        )


# ---------------------------------------------------------------------------
# Hybrid retrieval tests
# ---------------------------------------------------------------------------


def test_hybrid_scores_in_range():
    """All final hybrid scores should be between 0 and 1."""
    results = hybrid_search("how long does shipping take", top_k=5)
    for r in results:
        assert 0.0 <= r["final_score"] <= 1.0, (
            f"Hybrid final_score out of range: {r['final_score']}"
        )


def test_hybrid_deduplication():
    """There should be no duplicate (filename, chunk_index) pairs in hybrid results."""
    results = hybrid_search("return refund policy 30 days", top_k=10)
    seen = set()
    for r in results:
        key = (r["filename"], r["chunk_index"])
        assert key not in seen, f"Duplicate chunk found in hybrid results: {key}"
        seen.add(key)


def test_hybrid_formula():
    """
    Verify the 0.45/0.55 weighting formula is correctly applied.

    For every result where both bm25_score and vector_score are non-zero,
    the final_score should match the formula within floating-point tolerance.
    """
    results = hybrid_search("payment methods Klarna Afterpay", top_k=5)
    for r in results:
        expected = (
            settings.BM25_WEIGHT * r["bm25_score"]
            + settings.VECTOR_WEIGHT * r["vector_score"]
        )
        assert abs(r["final_score"] - expected) < 1e-4, (
            f"Hybrid formula mismatch: got {r['final_score']:.6f}, "
            f"expected {expected:.6f}"
        )


def test_hybrid_result_structure():
    """Each hybrid result should contain all required keys."""
    results = hybrid_search("how to enable 2FA on my account", top_k=5)
    for r in results:
        assert "chunk_text" in r
        assert "filename" in r
        assert "chunk_index" in r
        assert "final_score" in r
        assert "bm25_score" in r
        assert "vector_score" in r


def test_hybrid_sorted_descending():
    """Results should be sorted by final_score in descending order."""
    results = hybrid_search("exchange size color variant", top_k=5)
    scores = [r["final_score"] for r in results]
    assert scores == sorted(scores, reverse=True), (
        "Hybrid results are not sorted by final_score descending"
    )
