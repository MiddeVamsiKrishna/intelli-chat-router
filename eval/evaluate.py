"""
eval/evaluate.py

Runs the test dataset (eval/test_dataset.json) through the hybrid intent
router and measures accuracy — overall, and broken down by category
(clear, ambiguous, multi_step, sensitive).

Also records which method (rule_based vs llm_based) handled each case,
which is useful evidence for the "approach comparison" section of REPORT.md.

Run with:
    python -m eval.evaluate
"""

import json
import os
import time
from intent.router import detect_intent


def detect_intent_with_retry(message, max_retries=3):
    """Wraps detect_intent with retries to handle transient Gemini 503 errors
    (server overload) separately from real failures."""
    for attempt in range(max_retries):
        try:
            return detect_intent(message)
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                wait_time = 15 * (attempt + 1)
                print(f"   (Gemini temporarily overloaded, retrying in {wait_time}s...)")
                time.sleep(wait_time)
            else:
                raise
    # If all retries failed, fall back to a safe default rather than crashing
    print("   (All retries failed, marking as 'unknown')")
    return {"intent": "unknown", "confidence": 0.0, "method": "llm_based_failed"}

EVAL_DIR = os.path.dirname(__file__)
TEST_DATASET_PATH = os.path.join(EVAL_DIR, "test_dataset.json")
RESULTS_PATH = os.path.join(EVAL_DIR, "results.json")


def run_evaluation():
    with open(TEST_DATASET_PATH, "r") as f:
        test_cases = json.load(f)

    results = []
    category_stats = {}  # category -> {"correct": n, "total": n}
    method_stats = {}    # method -> count

    for case in test_cases:
        message = case["message"]
        expected = case["expected_intent"]
        category = case["category"]

        detected = detect_intent_with_retry(message)
        actual_intent = detected["intent"]
        method = detected["method"]
        confidence = detected["confidence"]

        is_correct = actual_intent == expected

        results.append({
            "id": case["id"],
            "category": category,
            "message": message,
            "expected_intent": expected,
            "actual_intent": actual_intent,
            "correct": is_correct,
            "confidence": confidence,
            "method": method,
        })

        # Track per-category accuracy
        category_stats.setdefault(category, {"correct": 0, "total": 0})
        category_stats[category]["total"] += 1
        if is_correct:
            category_stats[category]["correct"] += 1

        # Track which method handled how many requests
        method_stats[method] = method_stats.get(method, 0) + 1

        status_symbol = "PASS" if is_correct else "FAIL"
        print(f"[{status_symbol}] {case['id']} ({category}) | '{message}'")
        print(f"       expected: {expected} | got: {actual_intent} | method: {method}\n")

        # Gemini free tier allows only 5 requests/minute for LLM-based calls.
        # Pause briefly after any case that used the LLM to stay under that limit.
        if method == "llm_based":
            time.sleep(13)

    # Overall accuracy
    total_correct = sum(1 for r in results if r["correct"])
    total_cases = len(results)
    overall_accuracy = total_correct / total_cases * 100

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Overall accuracy: {total_correct}/{total_cases} ({overall_accuracy:.1f}%)\n")

    print("Accuracy by category:")
    for category, stats in category_stats.items():
        acc = stats["correct"] / stats["total"] * 100
        print(f"  {category:12s}: {stats['correct']}/{stats['total']} ({acc:.1f}%)")

    print("\nRequests handled by method:")
    for method, count in method_stats.items():
        pct = count / total_cases * 100
        print(f"  {method:12s}: {count}/{total_cases} ({pct:.1f}%)")

    # Save detailed results for the report
    summary = {
        "overall_accuracy": overall_accuracy,
        "total_cases": total_cases,
        "total_correct": total_correct,
        "category_breakdown": {
            cat: {
                "correct": stats["correct"],
                "total": stats["total"],
                "accuracy_pct": round(stats["correct"] / stats["total"] * 100, 1),
            }
            for cat, stats in category_stats.items()
        },
        "method_breakdown": method_stats,
        "detailed_results": results,
    }

    with open(RESULTS_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nDetailed results saved to: {RESULTS_PATH}")
    return summary


if __name__ == "__main__":
    run_evaluation()
