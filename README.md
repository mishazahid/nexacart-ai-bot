# NexaCart AI Support Bot

A production-ready **RAG (Retrieval-Augmented Generation)** customer support chatbot built with FastAPI, React, and OpenAI. It answers customer questions about shipping, returns, exchanges, payments, and account management using a hybrid BM25 + FAISS retrieval pipeline.

---

## Features

- **Hybrid Retrieval** — Combines BM25 keyword search (weight 0.45) and FAISS dense vector search (weight 0.55) for best-of-both recall and precision
- **Confidence Scoring** — Weighted scoring of top-3 results; falls back to a human-support escalation message below the threshold
- **Streaming-ready FastAPI** backend with SQLite chat logging
- **React 18 frontend** with Tailwind CSS, animated typing indicator, collapsible source cards, and confidence badges
- **Fully Dockerised** with Docker Compose for one-command deployment
- **50-question eval dataset** and pytest test suite for ingestion, retrieval, and API

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User / Browser                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (port 3000)
┌──────────────────────────▼──────────────────────────────────┐
│               React Frontend (Tailwind CSS)                 │
│  WelcomeScreen · ChatWindow · MessageBubble · SourceCard    │
│  ConfidenceBadge · InputBar · TypingIndicator               │
└──────────────────────────┬──────────────────────────────────┘
                           │ POST /chat  (port 8000)
┌──────────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend                             │
│  /chat  · /ingest  · /health                                │
└──────────┬───────────────────────────────────────────────────┘
           │
   ┌───────▼────────────────────────────────┐
   │         Hybrid Retrieval Layer         │
   │  ┌──────────────┐  ┌────────────────┐  │
   │  │  BM25 Search │  │  FAISS Vector  │  │
   │  │  (weight 0.45│  │  (weight 0.55) │  │
   │  └──────┬───────┘  └───────┬────────┘  │
   │         └────────┬─────────┘           │
   │                  │ Weighted fusion      │
   │         final_score = 0.45*bm25        │
   │                        + 0.55*vector   │
   └──────────────────┬─────────────────────┘
                      │ Top-K chunks + confidence score
   ┌──────────────────▼──────────────────────────────────────┐
   │               Confidence Scorer                         │
   │  score ≥ 0.35 → OpenAI GPT-3.5                          │
   │  score < 0.35 → Fallback escalation message             │
   └──────────────────┬──────────────────────────────────────┘
                      │
   ┌──────────────────▼──────────────────────────────────────┐
   │              OpenAI Chat Completions API                 │
   │         (gpt-3.5-turbo, temperature 0.2)                 │
   └─────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- An **OpenAI API key** (`gpt-3.5-turbo` access)
- Docker + Docker Compose (for containerised deployment only)

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd nexacart-ai-support-bot
```

### 2. Configure the backend environment

```bash
cd backend
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY and INGEST_KEY
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the ingestion pipeline

This step loads the Markdown knowledge base, chunks it, generates embeddings,
and builds the FAISS + BM25 indexes.

```bash
python src/ingestion/pipeline.py
```

Expected output:
```
Ingestion Summary:
  status: success
  total_docs: 5
  total_chunks: 42
  time_taken_seconds: 8.34
```

### 5. Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

API is now available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### 6. Start the frontend

In a separate terminal:

```bash
cd frontend
npm install
npm start
```

Frontend is now available at `http://localhost:3000`.

---

## API Documentation

### `POST /chat`

Send a customer support query.

**Request:**
```json
{
  "query": "How long does shipping take?",
  "session_id": "optional-uuid-for-session-continuity"
}
```

**Response:**
```json
{
  "answer": "Standard shipping takes 3–5 business days for $4.99...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "confidence_score": 0.82,
  "is_fallback": false,
  "sources": [
    {
      "filename": "shipping_policy.md",
      "chunk_preview": "Standard shipping: 3–5 business days, $4.99 flat fee...",
      "score": 0.87
    }
  ],
  "query": "How long does shipping take?"
}
```

---

### `POST /ingest`

Rebuild the knowledge base indexes from Markdown files.

**Headers:** `X-Ingest-Key: <your INGEST_KEY>`

**Response:**
```json
{
  "status": "success",
  "total_docs": 5,
  "total_chunks": 42,
  "time_taken_seconds": 8.34
}
```

Returns `403` if the key is missing or incorrect.

---

### `GET /health`

Liveness/readiness probe.

**Response:**
```json
{
  "status": "ok",
  "index_loaded": true,
  "version": "1.0.0",
  "timestamp": "2025-01-15T14:32:00.123456"
}
```

---

## How Hybrid Retrieval Works

The bot uses **two complementary retrieval methods** fused by a weighted formula:

| Component | Method | Weight |
|-----------|--------|--------|
| BM25 (Okapi BM25) | Keyword frequency + IDF | **0.45** |
| FAISS vector search | Sentence embeddings (all-MiniLM-L6-v2) | **0.55** |

**Fusion formula:**
```
final_score = 0.45 × bm25_score + 0.55 × vector_score
```

- **BM25** excels at exact keyword matching (policy names, product names, specific terms)
- **Vector search** excels at semantic similarity (paraphrased questions, conceptual queries)
- **Weighted fusion** combines both so neither lexical nor semantic queries fall through

**Confidence scoring** uses a weighted average of the top-3 results:
- 1st result: 50% weight
- 2nd result: 30% weight
- 3rd result: 20% weight

If the final score is below `0.35`, the bot escalates to a human support message rather than hallucinating.

---

## Docker Deployment

### Build and start all services

```bash
# 1. Copy and fill in .env
cp backend/.env.example backend/.env
# Edit backend/.env with your OPENAI_API_KEY

# 2. Start services
docker compose up --build -d

# 3. Run the ingestion pipeline inside the backend container
docker compose exec backend python src/ingestion/pipeline.py

# 4. Verify health
curl http://localhost:8000/health
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

### Stop services

```bash
docker compose down
```

---

## Running Tests

```bash
cd backend

# Run ingestion first (creates indexes)
python src/ingestion/pipeline.py

# Run all tests
pytest tests/ -v

# Run specific suites
pytest tests/test_ingestion.py -v
pytest tests/test_retrieval.py -v
pytest tests/test_api.py -v
```

---

## Project Structure

```
nexacart-ai-support-bot/
├── backend/
│   ├── app/               # FastAPI app: config, models, DB, logger, main
│   ├── knowledge_base/    # 5 Markdown policy files
│   ├── src/
│   │   ├── ingestion/     # Document loader, chunker, pipeline
│   │   ├── retrieval/     # BM25, vector, and hybrid search
│   │   ├── llm/           # Prompt builder and OpenAI generator
│   │   └── confidence/    # Scorer and fallback logic
│   ├── data/              # FAISS index, BM25 pickle, SQLite DB, logs
│   └── tests/             # pytest suites + 50-question eval dataset
└── frontend/
    ├── public/            # index.html
    └── src/
        ├── api/           # Axios API client
        ├── components/    # React components
        ├── hooks/         # useChat custom hook
        ├── styles/        # Tailwind + custom CSS
        └── utils/         # Helper functions
```
