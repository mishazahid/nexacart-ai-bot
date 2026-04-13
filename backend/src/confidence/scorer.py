"""
NexaCart AI Support Bot - Confidence Scorer

Computes a weighted confidence score from hybrid retrieval results, decides
whether to answer or escalate, and formats source references for the API
response.
"""
from typing import Dict, List

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# Weights assigned to the top-3 results
_POSITION_WEIGHTS = [0.5, 0.3, 0.2]


def calculate_confidence(results: List[Dict]) -> float:
    """
    Compute a confidence score from the top hybrid-retrieval results.

    The score is a weighted average of the ``final_score`` values of the
    top three results:

    - 1st result: weight 0.50
    - 2nd result: weight 0.30
    - 3rd result: weight 0.20

    If fewer than three results are available, remaining weight is dropped
    (not redistributed) so the score reflects genuine uncertainty.

    Args:
        results: List of result dicts from :func:`hybrid_retrieval.hybrid_search`,
            sorted by ``final_score`` descending.

    Returns:
        A confidence score in the range [0.0, 1.0].  Returns 0.0 when
        ``results`` is empty.
    """
    if not results:
        logger.debug("No retrieval results — confidence = 0.0")
        return 0.0

    score = 0.0
    for i, weight in enumerate(_POSITION_WEIGHTS):
        if i < len(results):
            score += weight * results[i].get("final_score", 0.0)

    clamped = max(0.0, min(1.0, score))
    logger.debug("Confidence score calculated: %.4f", clamped)
    return clamped


def is_confident(score: float, threshold: float = settings.CONFIDENCE_THRESHOLD) -> bool:
    """
    Determine whether the confidence score exceeds the acceptable threshold.

    Args:
        score: The confidence score returned by :func:`calculate_confidence`.
        threshold: Minimum score required to proceed with an LLM answer.

    Returns:
        ``True`` if ``score >= threshold``, ``False`` otherwise.
    """
    return score >= threshold


def get_fallback_response() -> str:
    """
    Return the standard escalation message used when confidence is too low.

    Returns:
        A polite message directing the customer to human support.
    """
    return (
        "I'm not confident enough to answer that accurately based on our knowledge base. "
        "Please contact our support team at support@nexacart.com or call "
        "1-800-NEXACART (Mon–Fri, 9 AM–6 PM EST) for personalized assistance."
    )


def format_sources(results: List[Dict]) -> List[Dict]:
    """
    Format retrieval results into concise source references for the API response.

    Args:
        results: List of result dicts from :func:`hybrid_retrieval.hybrid_search`.

    Returns:
        List of source dicts, each containing:
        - ``filename`` (str): Source file name.
        - ``chunk_preview`` (str): First 150 characters of the chunk text.
        - ``score`` (float): The ``final_score`` of this chunk.
    """
    sources: List[Dict] = []
    for item in results:
        preview = item.get("chunk_text", "")[:150]
        sources.append(
            {
                "filename": item.get("filename", ""),
                "chunk_preview": preview,
                "score": round(item.get("final_score", 0.0), 4),
            }
        )
    return sources
