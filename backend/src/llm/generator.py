"""
NexaCart AI Support Bot - Answer Generator

Calls the OpenAI Chat Completions API and returns the generated answer along
with token usage statistics.
"""
from typing import Dict, List

import openai

from app.config import settings
from app.logger import get_logger
from src.llm.prompt_builder import build_messages

logger = get_logger(__name__)

# Initialise the OpenAI client once at module import time
_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_answer(query: str, context_chunks: List[Dict], history: List[Dict] = None) -> Dict:
    """
    Generate a customer support answer using the OpenAI Chat Completions API.

    Builds a prompt from the retrieved context chunks and the customer query,
    then calls the configured OpenAI model.

    Args:
        query: The customer's natural-language question.
        context_chunks: List of chunk dicts (must contain ``filename`` and
            ``chunk_text`` keys) returned by the retrieval layer.

    Returns:
        A dict containing:
        - ``answer`` (str): The model's response text.
        - ``model`` (str): The model identifier used.
        - ``prompt_tokens`` (int): Tokens consumed by the prompt.
        - ``completion_tokens`` (int): Tokens in the completion.
        - ``total_tokens`` (int): Total tokens used.

        On error, ``answer`` is set to a user-friendly error message and token
        counts are 0.
    """
    messages = build_messages(query, context_chunks, history=history)

    try:
        response = _client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,  # type: ignore[arg-type]
            temperature=0.2,
            max_tokens=512,
        )
        answer = response.choices[0].message.content or ""
        usage = response.usage

        logger.debug(
            "LLM response generated: model=%s tokens=%d",
            response.model,
            usage.total_tokens if usage else 0,
        )

        return {
            "answer": answer.strip(),
            "model": response.model,
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
        }

    except openai.RateLimitError as exc:
        logger.error("OpenAI rate limit exceeded: %s", exc)
        return {
            "answer": (
                "I'm currently experiencing high demand. Please try again in a moment "
                "or contact support at support@nexacart.com."
            ),
            "model": settings.OPENAI_MODEL,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

    except openai.APIError as exc:
        logger.error("OpenAI API error: %s", exc)
        return {
            "answer": (
                "I'm having trouble connecting to our AI service right now. "
                "Please try again shortly or contact support@nexacart.com."
            ),
            "model": settings.OPENAI_MODEL,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

    except Exception as exc:
        logger.exception("Unexpected error during answer generation: %s", exc)
        return {
            "answer": (
                "An unexpected error occurred. Please contact our support team "
                "at support@nexacart.com for assistance."
            ),
            "model": settings.OPENAI_MODEL,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
