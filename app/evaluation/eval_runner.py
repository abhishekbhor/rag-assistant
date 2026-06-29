"""
RAG pipeline evaluation runner.

This module drives regression checks against the live query pipeline. The
evaluation folder is split intentionally:

  - eval_data.py  — test cases only (questions + expected_keywords). Add or edit
                    cases there; this file stays the runner logic.
  - eval_runner.py — runs each case through the pipeline and scores results.

Each test case is executed via run_query_pipeline() in query_service.py — the
same function used by POST /query and the CLI in main.py. That keeps eval
results aligned with what users see in production.

Results are also exposed over HTTP: GET /evaluate in api.py calls run_evaluation()
and returns JSON instead of printing a summary.
"""

from app.evaluation.eval_data import EVAL_SET
from app.services.query_service import run_query_pipeline


def answer_matches(answer: str, expected_keywords: list[str], min_matches: int = 1) -> bool:
    """
    Pass/fail check for a single test case.

    Keywords come from eval_data.py (expected_keywords). At least min_matches
    must appear in the answer (case-insensitive). This is a lightweight proxy
    for correctness — not semantic similarity or LLM-as-judge.
    """
    answer_lower = answer.lower()
    matches = sum(1 for keyword in expected_keywords if keyword.lower() in answer_lower)
    return matches >= min_matches


def run_evaluation(include_debug: bool = False):
    """
    Run every entry in EVAL_SET (eval_data.py) through the RAG pipeline.

    For each case, calls run_query_pipeline() — retrieval, reranking, and
    generation are identical to a real /query request. Set include_debug=True
    to attach timing and cache metadata from query_service (same flag as the API).

    Returns a list of per-case dicts (question, answer, passed, sources, …)
    consumed by print_evaluation_summary() or serialized by GET /evaluate in api.py.
    """
    results = []

    for test_case in EVAL_SET:
        question = test_case["question"]
        expected_keywords = test_case["expected_keywords"]

        result = run_query_pipeline(question, include_debug=include_debug)

        answer = result["answer"]
        passed = answer_matches(answer, expected_keywords)

        item = {
            "question": question,
            "expected_keywords": expected_keywords,
            "answer": answer,
            "passed": passed,
            "sources": result["sources"],
        }

        if include_debug and "debug" in result:
            item["debug"] = result["debug"]

        results.append(item)

    return results


def print_evaluation_summary(results):
    """
    Human-readable report for local runs (python -m app.evaluation.eval_runner).

    api.py returns the same results as JSON via GET /evaluate; use this function
    when debugging from the terminal.
    """
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print("\n=== Evaluation Summary ===")
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Accuracy: {passed / total:.1%}" if total else "Accuracy: N/A")

    print("\n=== Detailed Results ===")
    for i, r in enumerate(results, start=1):
        print(f"\n[{i}] Question: {r['question']}")
        print(f"Expected keywords: {r['expected_keywords']}")
        print(f"Passed: {r['passed']}")
        print(f"Answer: {r['answer']}")

        if "debug" in r:
            timing = r["debug"].get("timing_seconds", {})
            if timing:
                print(f"Timing: {timing}")

        print("Sources:")
        for src in r["sources"]:
            print(f"  - {src['source']} | chunk {src['chunk_index']}")
            print(f"    {src['preview']}")


if __name__ == "__main__":
    # Local entry point: mirrors GET /evaluate?include_debug=true in api.py
    results = run_evaluation(include_debug=True)
    print_evaluation_summary(results)
