from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class FeedbackStore:
    def __init__(self, file_path: str = "index/feedback.jsonl") -> None:
        self.path = Path(file_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save_feedback(
        self,
        question: str,
        answer: str,
        sources: list[dict[str, Any]],
        rating: int,
        notes: str | None = None,
    ) -> None:
        record = {
            "timestamp": time.time(),
            "question": question,
            "answer": answer,
            "sources": sources,
            "rating": rating,
            "notes": notes,
        }

        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


feedback_store = FeedbackStore()