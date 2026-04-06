from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator

from app.observability.metrics import metrics_logger


@contextmanager
def trace_block(name: str, payload: dict | None = None) -> Generator[None, None, None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        metrics_logger.log(
            event_type=name,
            duration_ms=duration_ms,
            payload=payload or {},
        )