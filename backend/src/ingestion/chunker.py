"""
NexaCart AI Support Bot - Document Chunker

Splits documents into overlapping word-based chunks suitable for embedding
and retrieval.
"""
from typing import Dict, List

from app.logger import get_logger

logger = get_logger(__name__)

_MIN_CHUNK_WORDS = 20


def chunk_document(
    content: str,
    filename: str,
    chunk_size: int = 200,
    overlap: int = 50,
) -> List[Dict]:
    """
    Split a document into overlapping word-based chunks.

    Each chunk has a sliding window of ``chunk_size`` words with ``overlap``
    words shared with the previous chunk.  Chunks shorter than
    ``_MIN_CHUNK_WORDS`` words are merged into the preceding chunk rather than
    being emitted as standalone records.

    Args:
        content: Full text of the document.
        filename: Source filename (used for provenance metadata).
        chunk_size: Target number of words per chunk.
        overlap: Number of words to repeat at the start of the next chunk.

    Returns:
        A list of chunk dicts, each containing:
        - ``chunk_text``: the text of this chunk
        - ``chunk_index``: 0-based position within the document
        - ``word_count``: number of words in this chunk
        - ``filename``: source filename
        - ``char_count``: character length of the chunk text
    """
    words: List[str] = content.split()
    if not words:
        logger.warning("Document %s is empty — no chunks generated.", filename)
        return []

    step = max(chunk_size - overlap, 1)
    raw_chunks: List[str] = []

    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        raw_chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += step

    # Merge undersized trailing chunks into the previous one
    merged: List[str] = []
    for chunk_text in raw_chunks:
        chunk_words = chunk_text.split()
        if merged and len(chunk_words) < _MIN_CHUNK_WORDS:
            merged[-1] = merged[-1] + " " + chunk_text
        else:
            merged.append(chunk_text)

    chunks: List[Dict] = []
    for idx, chunk_text in enumerate(merged):
        wc = len(chunk_text.split())
        chunks.append(
            {
                "chunk_text": chunk_text.strip(),
                "chunk_index": idx,
                "word_count": wc,
                "filename": filename,
                "char_count": len(chunk_text),
            }
        )

    logger.debug(
        "Chunked %s into %d chunks (chunk_size=%d, overlap=%d)",
        filename,
        len(chunks),
        chunk_size,
        overlap,
    )
    return chunks


def chunk_all_documents(
    documents: List[Dict],
    chunk_size: int = 200,
    overlap: int = 50,
) -> List[Dict]:
    """
    Chunk every document in the provided list.

    Args:
        documents: List of document dicts as returned by :func:`loader.load_documents`.
        chunk_size: Target chunk size in words.
        overlap: Overlap in words between consecutive chunks.

    Returns:
        Flat list of all chunk dicts across all documents.
    """
    all_chunks: List[Dict] = []
    for doc in documents:
        chunks = chunk_document(
            content=doc["content"],
            filename=doc["filename"],
            chunk_size=chunk_size,
            overlap=overlap,
        )
        all_chunks.extend(chunks)

    logger.info(
        "Total chunks created from %d documents: %d",
        len(documents),
        len(all_chunks),
    )
    return all_chunks
