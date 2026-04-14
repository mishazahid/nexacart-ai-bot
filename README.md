# NexaCart AI Support Bot

A production-ready **RAG (Retrieval-Augmented Generation)** customer support chatbot for an e-commerce store. It answers customer questions about shipping, returns, exchanges, payments, and account management using a hybrid BM25 + FAISS vector retrieval pipeline powered by OpenAI.

**Live Demo:** [nexacart-ai-bot.vercel.app](https://nexacart-ai-bot-git-master-mishazahids-projects.vercel.app)

---

## Features

- **Hybrid Retrieval** — Combines BM25 keyword search (weight 0.45) and FAISS dense vector search (weight 0.55)
- **Confidence Scoring** — Weighted scoring of top-3 results; falls back to human-support escalation below threshold
- **Conversation History** — Passes last 6 turns to OpenAI for context-aware follow-up answers
- **Greeting Handler** — Detects greetings and small talk before triggering the RAG pipeline
- **FastAPI Backend** — REST API with SQLite chat logging
- **React 18 Frontend** — Tailwind CSS, typing indicator, collapsible source cards, confidence badges, online/offline status
- **Dockerised** — Both services have Dockerfiles for containerised deployment
- **50-question Eval Dataset** — Covers all 5 topics with edge cases
- **pytest Test Suite** — Tests for ingestion, retrieval, and API

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector DB | FAISS (CPU) |
| Keyword Search | BM25 (rank-bm25) |
| LLM | OpenAI GPT-3.5-turbo |
| Database | SQLite (via SQLAlchemy) |
| Deployment | Vercel (frontend) + Railway (backend) |

---

## Architecture

```
User → React Frontend (Vercel)
           ↓ POST /chat
       FastAPI Backend (Railway)
           ↓
    Hybrid Retrieval Layer
    ┌─────────────┐  ┌──────────────┐
    │ BM25 Search │  │ FAISS Vector │
    │  (0.45)     │  │  (0.55)      │
    └──────┬──────┘  └──────┬───────┘
           └────────┬────────┘
              Weighted Fusion
         final_score = 0.45×bm25 + 0.55×vector
                    ↓
          Confidence Scorer
          score ≥ 0.35 → OpenAI GPT-3.5-turbo
          score < 0.35 → Fallback escalation
```

---

## Knowledge Base

The bot answers questions from 5 Markdown policy files:

| File | Topics Covered |
|---|---|
| `shipping_policy.md` | Shipping times, costs, carriers, tracking, free shipping |
| `return_policy.md` | Return window, refunds, non-returnable items, store credit |
| `exchange_policy.md` | Exchange process, pricing differences, international orders |
| `payment_methods.md` | Accepted methods, BNPL, gift cards, promo codes, failed payments |
| `account_help.md` | Password reset, 2FA, order history, account deletion, data download |

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+
- OpenAI API key

### 1. Clone the repository

```bash
git clone https://github.com/mishazahid/nexacart-ai-bot.git
cd nexacart-ai-bot
```

### 2. Set up the backend

```bash
cd backend

# Create .env file
copy .env.example .env   # Windows
# OR
cp .env.example .env     # Mac/Linux

# Edit .env and add your OPENAI_API_KEY
```

**.env file contents:**
```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=all-MiniLM-L6-v2
CONFIDENCE_THRESHOLD=0.35
DATABASE_URL=sqlite:///data/nexacart.db
LOG_LEVEL=INFO
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Run the ingestion pipeline

In a new terminal:

```powershell
# Windows PowerShell
Invoke-WebRequest -Uri http://localhost:8000/ingest -Method POST

# Mac/Linux
curl -X POST http://localhost:8000/ingest
```

### 6. Start the frontend

In another terminal:

```bash
cd frontend
npm install
npm start
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/docs`

---

## API Reference

### `POST /chat`

Send a customer support query.

**Request:**
```json
{
  "query": "How long does shipping take?",
  "session_id": "optional-uuid",
  "history": [
    { "role": "user", "content": "previous question" },
    { "role": "assistant", "content": "previous answer" }
  ]
}
```

**Response:**
```json
{
  "answer": "Standard shipping takes 3–5 business days for $4.99.",
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

### `POST /ingest`

Rebuild the knowledge base indexes from Markdown files.

```json
{
  "status": "success",
  "total_docs": 5,
  "total_chunks": 42,
  "time_taken_seconds": 8.34
}
```

### `GET /health`

Liveness/readiness probe.

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

| Component | Method | Weight |
|---|---|---|
| BM25 | Keyword frequency + IDF | 0.45 |
| FAISS | Sentence embeddings (all-MiniLM-L6-v2) | 0.55 |

```
final_score = 0.45 × bm25_score + 0.55 × vector_score
```

**Confidence scoring** uses a weighted average of the top-3 results:
- 1st result: 50% weight
- 2nd result: 30% weight
- 3rd result: 20% weight

If the final score is below `0.35`, the bot returns a fallback escalation message instead of hallucinating.

---

## Deployment

### Frontend — Vercel

1. Connect GitHub repo on [vercel.com](https://vercel.com)
2. Set Root Directory: `frontend`
3. Add environment variable: `REACT_APP_API_URL=<your-railway-backend-url>`
4. Deploy

### Backend — Railway

1. Connect GitHub repo on [railway.app](https://railway.app)
2. Set Root Directory: `backend`
3. Builder: `Dockerfile` (auto-detected)
4. Add environment variables:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL=gpt-3.5-turbo`
   - `EMBEDDING_MODEL=all-MiniLM-L6-v2`
   - `CONFIDENCE_THRESHOLD=0.35`
5. Deploy

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Project Structure

```
nexacart-ai-bot/
├── backend/
│   ├── app/                  # FastAPI app (config, models, DB, logger, main)
│   ├── knowledge_base/       # 5 Markdown policy files
│   ├── src/
│   │   ├── ingestion/        # Document loader, chunker, pipeline
│   │   ├── retrieval/        # BM25, vector, and hybrid search
│   │   ├── llm/              # Prompt builder and OpenAI generator
│   │   └── confidence/       # Scorer and fallback logic
│   ├── tests/                # pytest suites + 50-question eval dataset
│   ├── Dockerfile
│   ├── requirements.txt
│   └── start.sh              # Startup script (runs ingestion then server)
└── frontend/
    ├── public/
    └── src/
        ├── api/              # Axios API client
        ├── components/       # React UI components
        ├── hooks/            # useChat custom hook
        ├── styles/           # Tailwind + custom CSS
        └── utils/            # Helper functions
```

---

## Author

Built by **Misha** — [github.com/mishazahid](https://github.com/mishazahid)
