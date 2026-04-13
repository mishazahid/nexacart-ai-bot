"""
NexaCart AI Support Bot - Application Configuration

Loads settings from environment variables and .env file using pydantic-settings.
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", description="OpenAI chat model to use")

    # Embedding Configuration
    EMBEDDING_MODEL: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence-transformers model for embeddings",
    )

    # Index Paths
    FAISS_INDEX_PATH: str = Field(
        default="data/faiss_index/index.faiss",
        description="Path to the FAISS index file",
    )
    CHUNKS_METADATA_PATH: str = Field(
        default="data/faiss_index/chunks.pkl",
        description="Path to the pickled chunks metadata",
    )
    BM25_INDEX_PATH: str = Field(
        default="data/faiss_index/bm25.pkl",
        description="Path to the pickled BM25 index",
    )

    # Knowledge Base
    KNOWLEDGE_BASE_PATH: str = Field(
        default="knowledge_base/",
        description="Directory containing Markdown knowledge base files",
    )

    # Chunking Parameters
    CHUNK_SIZE: int = Field(default=200, description="Target chunk size in words")
    CHUNK_OVERLAP: int = Field(default=50, description="Overlap between consecutive chunks in words")

    # Retrieval Parameters
    TOP_K_BM25: int = Field(default=5, description="Number of top BM25 results to retrieve")
    TOP_K_VECTOR: int = Field(default=5, description="Number of top vector search results to retrieve")
    BM25_WEIGHT: float = Field(default=0.45, description="Weight for BM25 score in hybrid retrieval")
    VECTOR_WEIGHT: float = Field(default=0.55, description="Weight for vector score in hybrid retrieval")

    # Confidence
    CONFIDENCE_THRESHOLD: float = Field(
        default=0.35,
        description="Minimum confidence score required to answer (below this triggers fallback)",
    )

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///data/nexacart.db",
        description="SQLAlchemy database connection URL",
    )

    # Logging
    LOG_PATH: str = Field(default="data/logs/app.log", description="Path to the application log file")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins",
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
