"""
NexaCart AI Support Bot - Document Loader

Reads Markdown files from the knowledge base directory and returns their
content as structured dictionaries.
"""
import os
from typing import Dict, List

from app.logger import get_logger

logger = get_logger(__name__)


def load_documents(kb_path: str) -> List[Dict]:
    """
    Load all Markdown (.md) documents from the given directory.

    Args:
        kb_path: Path to the knowledge base directory containing .md files.

    Returns:
        A list of document dicts, each containing:
        - ``filename``: base name of the file (e.g. ``shipping_policy.md``)
        - ``content``: full text content of the file
        - ``filepath``: absolute path to the file
        - ``char_count``: total number of characters in the content

    Raises:
        FileNotFoundError: If ``kb_path`` does not exist.
    """
    if not os.path.exists(kb_path):
        raise FileNotFoundError(f"Knowledge base path not found: {kb_path!r}")

    documents: List[Dict] = []

    md_files = sorted(
        f for f in os.listdir(kb_path) if f.endswith(".md")
    )

    if not md_files:
        logger.warning("No .md files found in knowledge base path: %s", kb_path)
        return documents

    for filename in md_files:
        filepath = os.path.join(kb_path, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                content = fh.read()

            doc: Dict = {
                "filename": filename,
                "content": content,
                "filepath": os.path.abspath(filepath),
                "char_count": len(content),
            }
            documents.append(doc)
            logger.info(
                "Loaded document: %s (%d chars)", filename, len(content)
            )
        except OSError as exc:
            logger.error("Failed to read file %s: %s", filepath, exc)

    logger.info("Total documents loaded: %d", len(documents))
    return documents
