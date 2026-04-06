from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional


LOG_DIR = Path("index")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "metrics.log"


logger = logging.getLogger("rag_assistant")
logger.setLevel(logging.INFO)

if not logger.handlers:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(file_handler)


@dataclass
class RetrievalResultMetric:
    doc_id: str
    chunk_id: str
    source: str
    vector_score: Optional[float] = None
    bm25_score: Optional[float] = None
    rerank_score: Optional[float] = None
    final_score: Optional[float] = None
    feedback_boost: Optional[float] = None


@dataclass
class RequestMetrics:
    query: str
    total_latency_ms: Optional[float] = None
    embed_latency_ms: Optional[float] = None
    bm25_latency_ms: Optional[float] = None
    search_latency_ms: Optional[float] = None
    rerank_latency_ms: Optional[float] = None
    prompt_latency_ms: Optional[float] = None
    llm_latency_ms: Optional[float] = None
    cache_hit: bool = False
    retrieval_results: Optional[List[RetrievalResultMetric]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsCollector:
    def __init__(self, query: str) -> None:
        self.request = RequestMetrics(query=query)
        self._start_time = time.perf_counter()

    @contextmanager
    def timer(self, field_name: str) -> Generator[None, None, None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            setattr(self.request, field_name, round(elapsed_ms, 2))

    def set_cache_hit(self, hit: bool) -> None:
        self.request.cache_hit = hit

    def set_retrieval_results(self, results: List[RetrievalResultMetric]) -> None:
        self.request.retrieval_results = results

    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        self.request.metadata = metadata

    def finalize(self) -> None:
        self.request.total_latency_ms = round(
            (time.perf_counter() - self._start_time) * 1000, 2
        )

    def to_dict(self) -> Dict[str, Any]:
        self.finalize()
        return self.request.to_dict()

    def log(self) -> None:
        logger.info(json.dumps(self.to_dict(), ensure_ascii=False))