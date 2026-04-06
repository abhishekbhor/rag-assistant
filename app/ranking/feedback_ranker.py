from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

from app.storage.feedback_store import FeedbackStore


class FeedbackRanker:
    def __init__(self, feedback_store: FeedbackStore) -> None:
        self.feedback_store = feedback_store
        self.chunk_reward_map = self._build_chunk_reward_map()

    def _build_chunk_reward_map(self) -> Dict[str, float]:
        feedback_rows = self.feedback_store.load_feedback()
        reward_map: Dict[str, List[int]] = defaultdict(list)

        for row in feedback_rows:
            rating = int(row.get("rating", 0))
            chunks = row.get("retrieved_chunks", [])
            for chunk in chunks:
                chunk_id = chunk.get("chunk_id")
                if chunk_id:
                    reward_map[chunk_id].append(rating)

        averaged: Dict[str, float] = {}
        for chunk_id, ratings in reward_map.items():
            averaged[chunk_id] = sum(ratings) / len(ratings)

        return averaged

    def rerank(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rescored: List[Tuple[float, Dict[str, Any]]] = []

        for chunk in chunks:
            base_score = float(chunk.get("score", 0.0))
            chunk_id = chunk.get("chunk_id", "")
            feedback_bonus = self.chunk_reward_map.get(chunk_id, 0.0) * 0.1
            final_score = base_score + feedback_bonus

            enriched = dict(chunk)
            enriched["feedback_bonus"] = round(feedback_bonus, 4)
            enriched["final_score"] = round(final_score, 4)
            rescored.append((final_score, enriched))

        rescored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in rescored]