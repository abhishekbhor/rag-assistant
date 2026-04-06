from app.evaluation.eval_data import EVAL_SET
from app.services.query_service import run_query_pipeline


def answer_matches(answer: str, expected_keywords: list[str], min_matches: int = 1) -> bool:
    answer_lower = answer.lower()
    matches = sum(1 for keyword in expected_keywords if keyword.lower() in answer_lower)
    return matches >= min_matches


def run_evaluation(include_debug: bool = False):
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
    results = run_evaluation(include_debug=True)
    print_evaluation_summary(results)