"""
Central configuration for the RAG assistant.

Loads environment variables from a local .env file (see .env.example for the
template). Every module that needs a secret, model name, or path should import
from here rather than calling os.getenv() directly.

Consumers by setting:

  OPENAI_API_KEY     — generation/llm.py, ingestion/embedder.py,
                       retrieval/rerank.py, providers/openai_provider.py
  EMBEDDING_PROVIDER — providers/factory.py (selects embedding backend)
  LLM_PROVIDER       — reserved for future LLM provider switching (not wired yet)
  EMBEDDING_MODEL    — ingestion/embedder.py, providers/openai_provider.py
  LLM_MODEL          — generation/llm.py
  CHUNK_SIZE         — intended for ingestion/chunker.py (chunker still defaults
                       to 500 inline; align there if you change this value)
  TOP_K              — retrieval/search.py (default FAISS neighbor count)
  INDEX_PATH         — storage/vector_store.py (FAISS index written by
                       services/ingestion_service.py, read by query_service.py)
  CHUNKS_PATH        — storage/metadata_store.py (chunk pickle; same write/read
                       path as the index via ingestion_service / query_service)
"""

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Provider configuration — factory.py reads EMBEDDING_PROVIDER; LLM_PROVIDER is for future use
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# Model names passed to OpenAI clients in embedder.py, llm.py, and openai_provider.py
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")

# Pipeline tuning — TOP_K feeds retrieval/search.py; CHUNK_SIZE targets ingestion/chunker.py
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
TOP_K = int(os.getenv("TOP_K", 10))

# On-disk artifacts shared between ingestion_service (write) and query_service (read)
INDEX_PATH = os.getenv("INDEX_PATH", "index/index.faiss")
CHUNKS_PATH = os.getenv("CHUNKS_PATH", "index/chunks.pkl")
