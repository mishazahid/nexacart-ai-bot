"""
NexaCart AI Support Bot - Prompt Builder

Constructs the system prompt, context block, and message list sent to the
OpenAI Chat Completions API.
"""
from typing import Dict, List


def build_system_prompt() -> str:
    """
    Return the system-level instruction for the language model.

    Returns:
        A string instructing the model to act as NexaCart's support assistant
        and to rely exclusively on the provided knowledge base context.
    """
    return (
        "You are NexaCart's friendly and knowledgeable AI customer support assistant. "
        "Use the provided knowledge base context to answer customer questions accurately. "
        "Always give a helpful answer if the context contains any relevant information, even if partial. "
        "Be conversational, empathetic, and concise. Use bullet points for lists. "
        "If the context does not contain the answer, acknowledge what you do know and suggest "
        "the customer contact support@nexacart.com or call 1-800-NEXACART for further help. "
        "Never make up information that is not in the context."
    )


def build_context_block(chunks: List[Dict]) -> str:
    """
    Format a list of retrieved chunks into a readable context block.

    Each chunk is prefixed with its source filename so the model can attribute
    information and the user can verify sources.

    Args:
        chunks: List of chunk dicts, each containing at minimum
            ``filename`` and ``chunk_text`` keys.

    Returns:
        A single multi-line string with all chunks separated by ``---``.
    """
    sections: List[str] = []
    for chunk in chunks:
        section = f"Source: {chunk['filename']}\n{chunk['chunk_text']}"
        sections.append(section)
    return "\n---\n".join(sections)


def build_messages(query: str, chunks: List[Dict], history: List[Dict] = None) -> List[Dict]:
    """
    Build the messages list for the OpenAI Chat Completions API.

    The messages list contains:
    1. A ``system`` message with the persona and grounding instructions.
    2. Previous conversation turns (if history is provided).
    3. A ``user`` message containing the retrieved context and the customer question.

    Args:
        query: The customer's raw question.
        chunks: Retrieved chunks to include as context.
        history: Optional list of previous conversation turns, each with
            ``role`` (``"user"`` or ``"assistant"``) and ``content`` keys.

    Returns:
        A list of message dicts compatible with the OpenAI ``messages``
        parameter.
    """
    system_prompt = build_system_prompt()
    context_block = build_context_block(chunks)

    messages = [{"role": "system", "content": system_prompt}]

    # Inject up to last 6 turns of conversation history for context
    if history:
        for turn in history[-6:]:
            if turn.get("role") in ("user", "assistant") and turn.get("content"):
                messages.append({"role": turn["role"], "content": turn["content"]})

    user_content = (
        f"Context:\n{context_block}\n\n"
        f"Customer Question: {query}"
    )
    messages.append({"role": "user", "content": user_content})

    return messages
