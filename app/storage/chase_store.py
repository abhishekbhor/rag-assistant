from __future__ import annotations

import hashlib
import json
import os
import pickle
import threading
import time
from pathlib import Path
from typing import Any, Optional


class FileCacheStore:
    def __init__(self, cache_dir: str = "index/cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _make_key(self, namespace: str, payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"{namespace}_{digest}.pkl"

    def get(self, namespace: str, payload: Any, ttl_seconds: Optional[int] = None) -> Optional[Any]:
        file_path = self.cache_dir / self._make_key(namespace, payload)
        if not file_path.exists():
            return None

        if ttl_seconds is not None:
            age = time.time() - os.path.getmtime(file_path)
            if age > ttl_seconds:
                return None

        with self._lock:
            with open(file_path, "rb") as f:
                return pickle.load(f)

    def set(self, namespace: str, payload: Any, value: Any) -> None:
        file_path = self.cache_dir / self._make_key(namespace, payload)
        with self._lock:
            with open(file_path, "wb") as f:
                pickle.dump(value, f)