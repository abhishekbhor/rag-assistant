from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import Any


class FileCache:
    def __init__(self, cache_dir: str) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_to_path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.pkl"

    def get(self, key: str) -> Any | None:
        path = self._key_to_path(key)
        if not path.exists():
            return None

        with path.open("rb") as f:
            return pickle.load(f)

    def set(self, key: str, value: Any) -> None:
        path = self._key_to_path(key)
        with path.open("wb") as f:
            pickle.dump(value, f)


response_cache = FileCache("index/cache/responses")
embedding_cache = FileCache("index/cache/embeddings")