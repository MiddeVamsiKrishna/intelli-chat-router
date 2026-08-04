"""
intent/router.py

Hybrid intent router — combines the rule-based and LLM-based detectors.

Strategy:
1. Try the rule-based detector first (fast, free, no API call).
2. If it can't confidently match (returns "unknown"), fall back to the
   LLM-based detector, which understands more natural/ambiguous phrasing.

This hybrid approach is the core design decision to explain in REPORT.md:
- Rule-based: instant, $0 cost, but brittle (misses anything not keyword-matched)
- LLM-based: handles natural language well, but slower and costs API calls
- Hybrid: gets the speed/cost benefit for clear requests, while still
  handling ambiguous ones correctly.
"""

from intent.rule_based import detect_intent_rule_based
from intent.llm_based import detect_intent_llm


def detect_intent(user_message: str):
    """
    Detect the user's intent using the hybrid strategy.

    Args:
        user_message: raw text from the user

    Returns:
        dict with:
            intent: str
            confidence: float
            method: "rule_based" or "llm_based" — useful for logging/evaluation
    """
    # Step 1: try rule-based first
    intent, confidence = detect_intent_rule_based(user_message)

    if intent != "unknown":
        return {
            "intent": intent,
            "confidence": confidence,
            "method": "rule_based",
        }

    # Step 2: fall back to LLM-based
    intent, confidence = detect_intent_llm(user_message)
    return {
        "intent": intent,
        "confidence": confidence,
        "method": "llm_based",
    }


if __name__ == "__main__":
    test_messages = [
        "Cancel my appointment please",       # rule-based should catch this
        "I need a refill for my medication",  # rule-based should catch this
        "Hi there",                            # falls back to LLM
        "My meds are running low, can you help?",  # falls back to LLM
        "I'm not feeling well and my chest hurts a bit",  # falls back to LLM
    ]

    for msg in test_messages:
        result = detect_intent(msg)
        print(
            f"'{msg}' -> intent: {result['intent']}, "
            f"confidence: {result['confidence']}, "
            f"method: {result['method']}"
        )
