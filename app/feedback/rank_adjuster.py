from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


class RankAdjuster:
    def __init__(self, feedback_file: str = "index/feedback.jsonl") -> None:
        self.feedback_file = Path(feedback_file)

    def _source_weights(self) -> dict[str, float]:
        if not self.feedback_file.exists():
            return {}

        totals = defaultdict(float)
        counts = defaultdict(int)

        with self.feedback_file.open("r", encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                rating = int(row.get("rating", 0))
                sources = row.get("sources", [])

                for source in sources:
                    key = self._source_key(source)
                    totals[key] += rating
                    counts[key] += 1

        weights: dict[str, float] = {}
        for key, total in totals.items():
            avg = total / counts[key]

            if avg >= 4:
                weights[key] = 1.0
            elif avg <= 2:
                weights[key] = -0.5
            else:
                weights[key] = 0.0

        return weights

    def _source_key(self, item: dict[str, Any]) -> str:
        source = str(item.get("source", "unknown"))
        chunk_index = item.get("chunk_index")
        return f"{source}::{chunk_index}"

    def adjust(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        weights = self._source_weights()
        adjusted: list[dict[str, Any]] = []

        for chunk in chunks:
            item = dict(chunk)
            key = self._source_key(item)
            boost = weights.get(key, 0.0)

            base_score = item.get("score")
            try:
                base_score = float(base_score) if base_score is not None else 0.0
            except (TypeError, ValueError):
                base_score = 0.0

            item["feedback_boost"] = boost
            item["score"] = base_score + boost
            adjusted.append(item)

        adjusted.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
        return adjusted


rank_adjuster = RankAdjuster()