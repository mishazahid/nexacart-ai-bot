"""
Tests for the ingestion pipeline — loader, chunker, and full pipeline.
"""
import os
import sys

import pytest

# Ensure the backend root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ingestion.chunker import chunk_all_documents, chunk_document
from src.ingestion.loader import load_documents
from src.ingestion.pipeline import run_ingestion
from app.config import settings


KNOWLEDGE_BASE_PATH = settings.KNOWLEDGE_BASE_PATH


# ---------------------------------------------------------------------------
# Loader tests
# ---------------------------------------------------------------------------


def test_loader_finds_files():
    """The knowledge base directory should contain exactly 5 Markdown documents."""
    documents = load_documents(KNOWLEDGE_BASE_PATH)
    assert len(documents) == 5, (
        f"Expected 5 documents, got {len(documents)}. "
        "Check that all 5 .md files exist in knowledge_base/."
    )


def test_loader_document_structure():
    """Each loaded document dict should have the required keys with non-empty values."""
    documents = load_documents(KNOWLEDGE_BASE_PATH)
    for doc in documents:
        assert "filename" in doc
        assert "content" in doc
        assert "filepath" in doc
        assert "char_count" in doc
        assert doc["filename"].endswith(".md")
        assert len(doc["content"]) > 0
        assert doc["char_count"] == len(doc["content"])


def test_loader_raises_for_missing_path():
    """FileNotFoundError should be raised when the knowledge base path does not exist."""
    with pytest.raises(FileNotFoundError):
        load_documents("/nonexistent/path/to/kb")


# ---------------------------------------------------------------------------
# Chunker tests
# ---------------------------------------------------------------------------


def test_chunker_word_count():
    """Every chunk produced should have between 20 and 250 words."""
    documents = load_documents(KNOWLEDGE_BASE_PATH)
    chunks = chunk_all_documents(documents, chunk_size=200, overlap=50)
    for chunk in chunks:
        assert chunk["word_count"] >= 20, (
            f"Chunk too small: {chunk['word_count']} words in {chunk['filename']} "
            f"(chunk_index={chunk['chunk_index']})"
        )
        assert chunk["word_count"] <= 250, (
            f"Chunk too large: {chunk['word_count']} words in {chunk['filename']} "
            f"(chunk_index={chunk['chunk_index']})"
        )


def test_chunker_overlap():
    """Consecutive chunks from the same document should share overlapping words."""
    content = " ".join([f"word{i}" for i in range(600)])
    chunks = chunk_document(content, filename="test.md", chunk_size=100, overlap=30)
    assert len(chunks) >= 2, "Expected at least two chunks from a 600-word document"

    chunk0_words = set(chunks[0]["chunk_text"].split())
    chunk1_words = set(chunks[1]["chunk_text"].split())
    overlap = chunk0_words & chunk1_words
    assert len(overlap) > 0, (
        "Expected overlapping words between consecutive chunks but found none."
    )


def test_chunker_no_empty_chunks():
    """No chunk should have empty text."""
    documents = load_documents(KNOWLEDGE_BASE_PATH)
    chunks = chunk_all_documents(documents)
    for chunk in chunks:
        assert chunk["chunk_text"].strip() != "", "Found an empty chunk"


def test_chunker_preserves_filename():
    """Each chunk should carry the filename of its source document."""
    documents = load_documents(KNOWLEDGE_BASE_PATH)
    chunks = chunk_all_documents(documents)
    source_filenames = {doc["filename"] for doc in documents}
    for chunk in chunks:
        assert chunk["filename"] in source_filenames, (
            f"Chunk filename {chunk['filename']!r} not in source documents"
        )


# ---------------------------------------------------------------------------
# Pipeline integration test
# ---------------------------------------------------------------------------


def test_pipeline_creates_index():
    """After run_ingestion(), the FAISS index and BM25 pickle files should exist."""
    result = run_ingestion()

    assert result["status"] == "success"
    assert result["total_docs"] == 5
    assert result["total_chunks"] > 0
    assert result["time_taken_seconds"] >= 0

    assert os.path.exists(settings.FAISS_INDEX_PATH), (
        f"FAISS index not found at {settings.FAISS_INDEX_PATH}"
    )
    assert os.path.exists(settings.BM25_INDEX_PATH), (
        f"BM25 index not found at {settings.BM25_INDEX_PATH}"
    )
    assert os.path.exists(settings.CHUNKS_METADATA_PATH), (
        f"Chunks metadata not found at {settings.CHUNKS_METADATA_PATH}"
    )
