from __future__ import annotations

from app.storage.vector_store import load_index
from app.storage.metadata_store import load_chunks
from app.retrieval.embed_query import embed_query
from app.retrieval.search import search
from app.retrieval.bm25_index import build_bm25_index, bm25_search
from app.retrieval.rerank import rerank
from app.generation.prompt import build_prompt
from app.generation.llm import generate_answer
from app.observability.metrics import MetricsCollector, RetrievalResultMetric
from app.feedback.rank_adjuster import rank_adjuster

try:
    from app.cache.cache_manager import response_cache
except ImportError:
    response_cache = None


def run_query_pipeline(question: str, include_debug: bool = False) -> dict:
    metrics = MetricsCollector(query=question)

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

    index = load_index()
    chunks = load_chunks()

    with metrics.timer("embed_latency_ms"):
        query_embedding = embed_query(question)

    with metrics.timer("bm25_latency_ms"):
        bm25, tokenized_corpus = build_bm25_index(chunks)
        bm25_indices = bm25_search(bm25, tokenized_corpus, question, k=5)

    with metrics.timer("search_latency_ms"):
        faiss_indices = search(index, query_embedding, k=5)

        faiss_indices = [int(i) for i in faiss_indices]
        bm25_indices = [int(i) for i in bm25_indices]

        combined_indices = list(dict.fromkeys(faiss_indices + bm25_indices))
        combined_indices = [int(i) for i in combined_indices]

        candidate_chunks = [chunks[i] for i in combined_indices]

    with metrics.timer("rerank_latency_ms"):
        reranked_chunks = rerank(question, candidate_chunks)
        adjusted_chunks = rank_adjuster.adjust(reranked_chunks)
        relevant_chunks = adjusted_chunks[:5]

    with metrics.timer("prompt_latency_ms"):
        prompt = build_prompt(question, relevant_chunks)

    with metrics.timer("llm_latency_ms"):
        answer = generate_answer(prompt)

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
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None