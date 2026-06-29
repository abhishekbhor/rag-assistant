"""
Evaluation test cases for the RAG pipeline.

This file holds data only — no pipeline logic. eval_runner.py imports EVAL_SET
and, for each entry, calls run_query_pipeline() (query_service.py) then checks
the answer with answer_matches().

Schema for each test case:
  - question          — sent to the pipeline as-is (same input as POST /query)
  - expected_keywords — substrings that should appear in the answer; eval_runner
                        passes the case if at least one matches (case-insensitive)

To add a regression test, append a dict to EVAL_SET below. Questions should
reflect facts present in the ingested corpus (see app/ingestion/). Run locally
with: python -m app.evaluation.eval_runner
Or hit GET /evaluate in api.py for JSON results.
"""

EVAL_SET = [
    # Factual retrieval — answer should name Tommy and his background
    {
        "question": "Who was Tommy?",
        "expected_keywords": ["Thomas", "Riordan", "brother", "soldier", "fighter"],
    },
    # Follow-up on the same narrative — any one keyword is enough to pass
    {
        "question": "Did Tommy win?",
        "expected_keywords": ["won", "fight", "Sparta"],
    },
    # Different topic in the corpus — tests retrieval across documents
    {
        "question": "What happened in Iraq?",
        "expected_keywords": ["Iraq", "tank", "Marine"],
    },
    # Unanswerable from context — pipeline should admit uncertainty, not hallucinate
    {
        "question": "What city did Tommy live in after the tournament?",
        "expected_keywords": ["i don't know"],
    },
]
