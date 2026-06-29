"""
Query (read) path for the RAG assistant.

The services folder splits the two end-to-end pipelines:

  - ingestion_service.py — load documents, chunk, embed, and persist the index
                           (app/ingestion/ + app/storage/). Run via POST /ingest
                           or `ingest` mode in main.py before querying.
  - query_service.py     — answer a question using that persisted index (this file).

run_query_pipeline() is the single entry point for question answering. 

Callers:

  - api.py POST /query        — HTTP API for clients
  - main.py                   — interactive CLI (`query` mode)
  - evaluation/eval_runner.py — regression tests over eval_data.EVAL_SET

Data written by ingestion_service is read here via load_index() and load_chunks()
(storage/). 
Retrieval (embed_query, search, bm25, rerank) narrows candidates;
generation (build_prompt, generate_answer) produces the final answer. 
User feedback from feedback_store.py can re-order results via rank_adjuster.
"""

from __future__ import annotations

# Persisted artifacts produced by ingestion_service (vector_store + metadata_store)
from app.storage.vector_store import load_index
from app.storage.metadata_store import load_chunks

# Hybrid retrieval: dense (FAISS) + sparse (BM25), then cross-encoder reranking
from app.retrieval.embed_query import embed_query
from app.retrieval.search import search
from app.retrieval.bm25_index import build_bm25_index, bm25_search
from app.retrieval.rerank import rerank

# LLM answer generation from retrieved context
from app.generation.prompt import build_prompt
from app.generation.llm import generate_answer

from app.observability.metrics import MetricsCollector, RetrievalResultMetric

# Applies boosts from past user ratings (feedback/feedback_store.py)
from app.feedback.rank_adjuster import rank_adjuster

# Optional response cache — skipped gracefully if app/cache is not installed
try:
    from app.cache.cache_manager import response_cache
except ImportError:
    response_cache = None


def run_query_pipeline(question: str, include_debug: bool = False) -> dict:
    """
    Run the full RAG pipeline for one question.

    Returns {"answer": str, "sources": list[dict], "debug": dict?}.
    sources entries match the SourceItem shape in api.py (source, chunk_index,
    preview). Pass include_debug=True to attach timing and retrieval metadata
    (used by main.py, eval_runner, and GET /evaluate).
    """
    metrics = MetricsCollector(query=question)

    # --- Cache lookup (same normalized key for repeated questions) ---
    normalized_query = " ".join(question.strip().lower().split())
    cache_key = f"response::{normalized_query}"

    if response_cache is not None:
        cached = response_cache.get(cache_key)
        if cached is not None:
            metrics.set_cache_hit(True)

            result = {
                "answer": cached["answer"],
                "sources": cached["sources"],
            }

            if include_debug:
                cached_debug = cached.get("debug", {}).copy()
                cached_debug["cache_hit"] = True
                result["debug"] = cached_debug

            metrics.log()
            return result

    metrics.set_cache_hit(False)

    # --- Load index and chunk metadata built by ingestion_service ---
    index = load_index()
    chunks = load_chunks()

    # --- Embed query, then hybrid retrieval (FAISS + BM25) ---
    with metrics.timer("embed_latency_ms"):
        query_embedding = embed_query(question)

    with metrics.timer("bm25_latency_ms"):
        bm25, tokenized_corpus = build_bm25_index(chunks)
        bm25_indices = bm25_search(bm25, tokenized_corpus, question, k=5)

    with metrics.timer("search_latency_ms"):
        faiss_indices = search(index, query_embedding, k=5)

        faiss_indices = [int(i) for i in faiss_indices]
        bm25_indices = [int(i) for i in bm25_indices]

        # Merge dense and sparse hits, preserving order and deduplicating
        combined_indices = list(dict.fromkeys(faiss_indices + bm25_indices))
        combined_indices = [int(i) for i in combined_indices]

        candidate_chunks = [chunks[i] for i in combined_indices]

    # --- Rerank, apply feedback boosts, keep top 5 for the prompt ---
    with metrics.timer("rerank_latency_ms"):
        reranked_chunks = rerank(question, candidate_chunks)
        adjusted_chunks = rank_adjuster.adjust(reranked_chunks)
        relevant_chunks = adjusted_chunks[:5]

    # --- Build prompt and call the LLM ---
    with metrics.timer("prompt_latency_ms"):
        prompt = build_prompt(question, relevant_chunks)

    with metrics.timer("llm_latency_ms"):
        answer = generate_answer(prompt)

    # --- Shape sources for API/eval consumers; record scores for observability ---
    sources = []
    retrieval_metrics = []

    for chunk in relevant_chunks:
        source = str(chunk.get("source", "unknown"))
        chunk_index = int(chunk.get("chunk_index", -1))
        preview = str(chunk.get("text", ""))[:200]

        sources.append(
            {
                "source": source,
                "chunk_index": chunk_index,
                "preview": preview,
            }
        )

        retrieval_metrics.append(
            RetrievalResultMetric(
                doc_id=str(chunk.get("doc_id", source)),
                chunk_id=str(chunk.get("chunk_id", f"{source}_{chunk_index}")),
                source=source,
                vector_score=_safe_float(chunk.get("vector_score")),
                bm25_score=_safe_float(chunk.get("bm25_score")),
                rerank_score=_safe_float(chunk.get("rerank_score")),
                final_score=_safe_float(chunk.get("score")),
                feedback_boost=_safe_float(chunk.get("feedback_boost")),
            )
        )

    metrics.set_retrieval_results(retrieval_metrics)
    metrics.set_metadata(
        {
            "top_k": len(relevant_chunks),
            "faiss_indices": faiss_indices,
            "bm25_indices": bm25_indices,
            "combined_indices": combined_indices,
        }
    )

    result = {
        "answer": answer,
        "sources": sources,
    }

    if include_debug:
        result["debug"] = metrics.to_dict()

    if response_cache is not None:
        response_cache.set(cache_key, result)

    metrics.log()
    return result


def _safe_float(value):
    """Coerce chunk score fields to float for MetricsCollector; missing values stay None."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
