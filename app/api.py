from typing import Any, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.services.query_service import run_query_pipeline
from app.services.ingestion_service import run_ingestion_pipeline
from app.evaluation.eval_runner import run_evaluation
from app.feedback.feedback_store import feedback_store

app = FastAPI(title="RAG Assistant API")


@app.get("/")
def root():
    return {"status": "ok", "message": "RAG Assistant API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


class QueryRequest(BaseModel):
    question: str
    include_debug: bool = False


class SourceItem(BaseModel):
    source: str
    chunk_index: int
    preview: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    debug: Optional[dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    question: str
    answer: str
    sources: list[SourceItem]
    rating: int = Field(..., ge=1, le=5)
    notes: Optional[str] = None


@app.post("/ingest")
def ingest():
    return run_ingestion_pipeline()


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    return run_query_pipeline(
        request.question,
        include_debug=request.include_debug,
    )


@app.post("/feedback")
def feedback(request: FeedbackRequest):
    feedback_store.save_feedback(
        question=request.question,
        answer=request.answer,
        sources=[s.model_dump() for s in request.sources],
        rating=request.rating,
        notes=request.notes,
    )
    return {"status": "success", "message": "Feedback recorded"}


@app.get("/evaluate")
def evaluate(include_debug: bool = False):
    results = run_evaluation(include_debug=include_debug)

    total = len(results)
    passed = sum(1 for r in results if r["passed"])

    return {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "accuracy": round(passed / total, 2) if total else 0,
        },
        "results": results,
    }