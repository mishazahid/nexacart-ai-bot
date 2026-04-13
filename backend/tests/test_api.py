"""
Integration tests for the FastAPI endpoints.

Uses HTTPX AsyncClient against the live application.  Requires the index
files to exist (run the ingestion pipeline first).
"""
import os
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from app.main import app


# ---------------------------------------------------------------------------
# Async test client fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="module")
async def client():
    """Yield an AsyncClient pointed at the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_health_returns_ok(client: AsyncClient):
    """GET /health should return HTTP 200 with status 'ok'."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "index_loaded" in data
    assert "version" in data
    assert "timestamp" in data


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_chat_returns_valid_schema(client: AsyncClient):
    """POST /chat should return the expected response schema."""
    payload = {"query": "How long does standard shipping take?"}
    response = await client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "answer" in data, "Response missing 'answer' field"
    assert "session_id" in data, "Response missing 'session_id' field"
    assert "confidence_score" in data, "Response missing 'confidence_score' field"
    assert "is_fallback" in data, "Response missing 'is_fallback' field"
    assert "sources" in data, "Response missing 'sources' field"
    assert "query" in data, "Response missing 'query' field"

    assert isinstance(data["answer"], str) and len(data["answer"]) > 0
    assert isinstance(data["sources"], list)


@pytest.mark.anyio
async def test_confidence_score_range(client: AsyncClient):
    """Confidence score should always be between 0.0 and 1.0."""
    queries = [
        "What is your return policy?",
        "How do I reset my password?",
        "Do you accept PayPal?",
    ]
    for query in queries:
        response = await client.post("/chat", json={"query": query})
        assert response.status_code == 200
        score = response.json()["confidence_score"]
        assert 0.0 <= score <= 1.0, (
            f"Confidence score out of range for query {query!r}: {score}"
        )


@pytest.mark.anyio
async def test_fallback_on_garbage_input(client: AsyncClient):
    """Completely unrelated input should trigger the fallback response."""
    response = await client.post(
        "/chat", json={"query": "asdfghjkl random xyz quantum banana 12345"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_fallback"] is True, (
        "Expected fallback=True for nonsense query but got fallback=False"
    )


@pytest.mark.anyio
async def test_session_id_persistence(client: AsyncClient):
    """Providing a session_id should result in the same session_id being echoed back."""
    test_session = "test-session-abc-123"
    response = await client.post(
        "/chat",
        json={"query": "What payment methods do you accept?", "session_id": test_session},
    )
    assert response.status_code == 200
    assert response.json()["session_id"] == test_session


@pytest.mark.anyio
async def test_auto_session_id_generated(client: AsyncClient):
    """When no session_id is provided, one should be generated automatically."""
    response = await client.post("/chat", json={"query": "How do I return an item?"})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["session_id"]) > 0


@pytest.mark.anyio
async def test_sources_structure(client: AsyncClient):
    """Each source in the response should have filename, chunk_preview, and score."""
    response = await client.post("/chat", json={"query": "What is the exchange policy?"})
    assert response.status_code == 200
    sources = response.json()["sources"]
    for source in sources:
        assert "filename" in source
        assert "chunk_preview" in source
        assert "score" in source
        assert isinstance(source["score"], float)


# ---------------------------------------------------------------------------
# Ingest endpoint
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_ingest_requires_auth(client: AsyncClient):
    """POST /ingest without a valid X-Ingest-Key header should return HTTP 403."""
    response = await client.post("/ingest")
    assert response.status_code == 403


@pytest.mark.anyio
async def test_ingest_wrong_key_rejected(client: AsyncClient):
    """POST /ingest with the wrong key should return HTTP 403."""
    response = await client.post(
        "/ingest", headers={"X-Ingest-Key": "wrong-key-12345"}
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_ingest_with_valid_key(client: AsyncClient):
    """POST /ingest with the correct key should return HTTP 200 and ingestion summary."""
    response = await client.post(
        "/ingest", headers={"X-Ingest-Key": settings.INGEST_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_docs"] > 0
    assert data["total_chunks"] > 0
    assert data["time_taken_seconds"] >= 0
