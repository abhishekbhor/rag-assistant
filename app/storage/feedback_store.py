from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class FeedbackStore:
    def __init__(self, feedback_file: str = "index/feedback.jsonl") -> None:
        self.feedback_path = Path(feedback_file)
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.feedback_path.exists():
            self.feedback_path.touch()

    def save_feedback(
        self,
        query: str,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]],
        rating: int,
        notes: str = "",
    ) -> None:
        record = {
            "query": query,
            "answer": answer,
            "retrieved_chunks": retrieved_chunks,
            "rating": rating,
            "notes": notes,
        }
        with open(self.feedback_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def load_feedback(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        with open(self.feedback_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows