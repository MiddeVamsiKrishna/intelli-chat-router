"""
intent/rule_based.py

Rule-based intent detector.
Uses simple keyword matching to detect user intent BEFORE falling back
to an LLM. This is fast (no API call) and handles the majority of
clear, straightforward requests.

Returns:
    (intent_name: str, confidence: float)

confidence is either 1.0 (rule matched) or 0.0 (no rule matched,
caller should fall back to the LLM-based detector).
"""

# Keyword -> intent mapping. Order matters: more specific rules first.
INTENT_KEYWORDS = {
    "book_appointment": ["book appointment", "book an appointment", "book a appointment", "schedule appointment", "schedule an appointment", "book a doctor", "make an appointment"],
    "cancel_appointment": ["cancel appointment", "cancel my appointment", "reschedule"],
    "check_appointment_status": ["appointment status", "check my appointment", "status of my appointment"],
    "request_refill": ["refill", "prescription refill", "renew prescription", "renew my medicine"],
    "find_doctor": ["find doctor", "find a doctor", "which doctor", "doctor for", "specialist for"],
    "faq": ["visiting hours", "insurance", "parking", "billing", "medical records", "emergency room"],
    "escalate_to_human": ["symptom", "pain", "diagnos", "advice", "what should i take", "i feel"],
}


def detect_intent_rule_based(user_message: str):
    """
    Check the user's message against known keyword patterns.

    Args:
        user_message: raw text from the user

    Returns:
        tuple(intent_name, confidence)
        If no rule matches, returns ("unknown", 0.0) so the hybrid router
        knows to fall back to the LLM-based detector.
    """
    message = user_message.lower().strip()

    for intent_name, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message:
                return intent_name, 1.0

    return "unknown", 0.0


if __name__ == "__main__":
    # Quick manual tests
    test_messages = [
        "I want to book an appointment with cardiology",
        "Cancel my appointment please",
        "What is the status of my appointment?",
        "I need a refill for my medication",
        "Find a doctor for dermatology",
        "What are your visiting hours?",
        "I have chest pain, what should I do?",
        "Hi there",  # should be unknown -> fallback to LLM
    ]

    for msg in test_messages:
        intent, confidence = detect_intent_rule_based(msg)
        print(f"'{msg}' -> intent: {intent}, confidence: {confidence}")
