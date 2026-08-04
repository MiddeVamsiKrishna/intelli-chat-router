"""
intent/llm_based.py

LLM-based intent detector.
Used as a FALLBACK when the rule-based detector can't confidently match
a user's message (see intent/rule_based.py). This uses an LLM to understand
more naturally-phrased or ambiguous requests, and returns a structured
(intent, confidence) response using LangChain's structured output feature.

Requires: GOOGLE_API_KEY set in your .env file (free tier available at
https://aistudio.google.com/app/apikey).
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal

load_dotenv()

# Must match the intent names used in intent/rule_based.py so the router
# can treat both detectors' outputs the same way.
INTENT_LABELS = [
    "book_appointment",
    "cancel_appointment",
    "check_appointment_status",
    "request_refill",
    "find_doctor",
    "faq",
    "escalate_to_human",
    "unknown",
]


class IntentResult(BaseModel):
    """Structured output schema the LLM must follow."""
    intent: Literal[
        "book_appointment",
        "cancel_appointment",
        "check_appointment_status",
        "request_refill",
        "find_doctor",
        "faq",
        "escalate_to_human",
        "unknown",
    ] = Field(description="The single best-matching intent for the user's message")
    confidence: float = Field(description="Confidence score between 0 and 1")


SYSTEM_PROMPT = """You are an intent classifier for a Healthcare Support Chatbot.
Classify the user's message into exactly ONE of these intents:

- book_appointment: user wants to schedule/book a new appointment
- cancel_appointment: user wants to cancel or reschedule an existing appointment
- check_appointment_status: user wants to check status of an appointment
- request_refill: user wants a prescription refill
- find_doctor: user wants to find a doctor/specialist/department
- faq: general informational question (hours, insurance, parking, billing, records)
- escalate_to_human: user describes symptoms, asks for medical advice/diagnosis,
  or anything the bot should NOT answer directly for safety reasons
- unknown: greeting, small talk, or anything that doesn't fit the above

Respond with the single best intent and a confidence score between 0 and 1.
"""


def get_llm_classifier():
    """Builds and returns a LangChain chain that outputs structured IntentResult."""
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
    structured_llm = llm.with_structured_output(IntentResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{user_message}"),
    ])

    return prompt | structured_llm


def detect_intent_llm(user_message: str):
    """
    Classify intent using the LLM.

    Args:
        user_message: raw text from the user

    Returns:
        tuple(intent_name: str, confidence: float)
    """
    if not os.getenv("GOOGLE_API_KEY"):
        raise EnvironmentError(
            "GOOGLE_API_KEY not found. Add it to your .env file before running this."
        )

    chain = get_llm_classifier()
    result: IntentResult = chain.invoke({"user_message": user_message})
    return result.intent, result.confidence


if __name__ == "__main__":
    # Quick manual tests — these are cases the rule-based detector
    # could NOT confidently handle, to show the LLM's value-add.
    test_messages = [
        "Hi there",
        "My meds are running low, can you help?",
        "I'm not feeling well and my chest hurts a bit",
        "Can you tell me who works in the skin department?",
    ]

    for msg in test_messages:
        try:
            intent, confidence = detect_intent_llm(msg)
            print(f"'{msg}' -> intent: {intent}, confidence: {confidence}")
        except EnvironmentError as e:
            print(e)
            break
