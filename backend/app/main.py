"""
NexaCart AI Support Bot - FastAPI Application Entry Point

Exposes three endpoints:
- POST /chat   — main conversational endpoint
- POST /ingest — rebuild the knowledge base indexes (protected)
- GET  /health — liveness/readiness probe
"""
import json
import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, create_tables, get_db
from app.logger import get_logger, log_interaction
from app.models import ChatLog
from src.confidence.scorer import (
    calculate_confidence,
    format_sources,
    get_fallback_response,
    is_confident,
)
from src.ingestion.pipeline import run_ingestion
from src.llm.generator import generate_answer
from src.retrieval.bm25_search import load_bm25_index
from src.retrieval.hybrid_retrieval import hybrid_search
from src.retrieval.vector_search import load_vector_index

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Greeting / small-talk handler
# ---------------------------------------------------------------------------

_GREETINGS = {
    "hi", "hello", "hey", "howdy", "hiya", "sup", "yo",
    "good morning", "good afternoon", "good evening", "good day",
    "thanks", "thank you", "thank you so much", "thanks a lot", "ty",
    "bye", "goodbye", "see you", "take care",
    "ok", "okay", "sure", "great", "cool", "got it", "alright",
}

_GREETING_RESPONSE = (
    "Hello! I'm NexaCart's AI support assistant. "
    "I can help you with:\n"
    "- Shipping & delivery\n"
    "- Returns & refunds\n"
    "- Exchanges\n"
    "- Payments & gift cards\n"
    "- Account & login issues\n\n"
    "What can I help you with today?"
)


def _is_greeting(text: str) -> bool:
    """Return True if the query is a greeting or small-talk phrase."""
    normalized = text.lower().strip().rstrip("!.,?")
    return normalized in _GREETINGS


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NexaCart AI Support Bot",
    description="RAG-based customer support chatbot powered by hybrid retrieval and OpenAI.",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Startup / shutdown lifecycle
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def startup_event() -> None:
    """Load indexes and create DB tables on application start."""
    logger.info("NexaCart AI Support Bot starting up…")
    try:
        load_bm25_index()
        load_vector_index()
    except FileNotFoundError:
        logger.warning(
            "Index files not found — run the ingestion pipeline before serving requests."
        )
    create_tables()
    logger.info("NexaCart AI Support Bot started successfully.")


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions."""
    logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a clean JSON payload for request validation errors."""
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "detail": str(exc)},
    )


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class HistoryItem(BaseModel):
    """A single turn in the conversation history."""

    role: str = Field(..., description="Either 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Payload for the /chat endpoint."""

    query: str = Field(..., min_length=1, max_length=1000, description="Customer question")
    session_id: Optional[str] = Field(None, description="Optional session UUID for continuity")
    history: Optional[List[HistoryItem]] = Field(None, description="Previous conversation turns")


class SourceItem(BaseModel):
    """A single knowledge base source reference."""

    filename: str
    chunk_preview: str
    score: float


class ChatResponse(BaseModel):
    """Response payload returned by the /chat endpoint."""

    answer: str
    session_id: str
    confidence_score: float
    is_fallback: bool
    sources: List[SourceItem]
    query: str


class IngestionResponse(BaseModel):
    """Response payload returned by the /ingest endpoint."""

    status: str
    total_docs: int
    total_chunks: int
    time_taken_seconds: float


class HealthResponse(BaseModel):
    """Response payload returned by the /health endpoint."""

    status: str
    index_loaded: bool
    version: str
    timestamp: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """
    Process a customer support query.

    1. Run hybrid retrieval (BM25 + vector).
    2. Calculate confidence.
    3. If confident, generate an LLM answer; otherwise return fallback message.
    4. Persist the interaction to the database.
    5. Return the structured response.
    """
    session_id = request.session_id or str(uuid.uuid4())
    query = request.query.strip()

    logger.info("Chat request | session=%s | query=%r", session_id, query[:80])

    # Greeting / small-talk short-circuit
    if _is_greeting(query):
        answer = _GREETING_RESPONSE
        confidence = 1.0
        sources = []
        is_fallback = False
    else:
        # Retrieval
        results = hybrid_search(query, top_k=5)

        # Confidence
        confidence = calculate_confidence(results)
        sources = format_sources(results)
        is_fallback = False

        history = [{"role": h.role, "content": h.content} for h in (request.history or [])]

        if is_confident(confidence):
            generation = generate_answer(query, results, history=history)
            answer = generation["answer"]
        else:
            answer = get_fallback_response()
            is_fallback = True
            logger.info(
                "Fallback triggered | session=%s | confidence=%.4f", session_id, confidence
            )

    # Persist to DB
    chat_log = ChatLog(
        id=str(uuid.uuid4()),
        session_id=session_id,
        query=query,
        response=answer,
        confidence_score=confidence,
        sources=json.dumps(sources),
        is_fallback=is_fallback,
        created_at=datetime.utcnow(),
    )
    db.add(chat_log)
    db.commit()

    # Structured log
    log_interaction(
        session_id=session_id,
        query=query,
        response=answer,
        confidence=confidence,
        is_fallback=is_fallback,
        sources=sources,
    )

    return ChatResponse(
        answer=answer,
        session_id=session_id,
        confidence_score=round(confidence, 4),
        is_fallback=is_fallback,
        sources=[SourceItem(**s) for s in sources],
        query=query,
    )


@app.post("/ingest", response_model=IngestionResponse)
async def ingest() -> IngestionResponse:
    """
    Rebuild the knowledge base indexes from the Markdown files.
    """

    logger.info("Ingestion requested via API.")
    result = run_ingestion()

    # Reload indexes into memory after re-ingestion
    try:
        load_bm25_index()
        load_vector_index()
    except Exception as exc:
        logger.error("Failed to reload indexes after ingestion: %s", exc)

    return IngestionResponse(
        status=result["status"],
        total_docs=result["total_docs"],
        total_chunks=result["total_chunks"],
        time_taken_seconds=result["time_taken_seconds"],
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Liveness and readiness probe.

    Returns whether the FAISS index file exists on disk so orchestration
    systems (Docker Compose, Kubernetes) can gate traffic until indexing
    completes.
    """
    index_loaded = os.path.exists(settings.FAISS_INDEX_PATH)
    return HealthResponse(
        status="ok",
        index_loaded=index_loaded,
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
    )
