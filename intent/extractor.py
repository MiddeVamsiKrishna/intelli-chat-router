"""
intent/extractor.py

Once we know the INTENT (from router.py), we still need to extract the
actual parameters to call the matching tool function with — e.g. for
book_appointment we need patient_name, department, and date pulled out
of the user's natural-language message.

This uses the LLM to extract those fields as JSON.
"""

import os
import json
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# Which fields each intent's tool function needs (must match tools/tools.py signatures)
INTENT_FIELDS = {
    "book_appointment": ["patient_name", "department", "date"],
    "cancel_appointment": ["appointment_id"],
    "check_appointment_status": ["appointment_id"],
    "request_refill": ["patient_id", "medication"],
    "find_doctor": ["specialty"],
    "escalate_to_human": ["reason"],
}

EXTRACTION_PROMPT = """Extract the following fields from the user's message as a JSON object.
Fields to extract: {fields}

Rules:
- If a field is not mentioned in the message, use the string "unknown" as its value.
- Respond with ONLY the JSON object, no other text, no markdown code fences.
- For "date" fields, use YYYY-MM-DD format if a specific date is given, otherwise "unknown".
- For "reason" in escalate_to_human, summarize the user's concern briefly.

User message: {user_message}
"""


def extract_entities(user_message: str, intent: str) -> dict:
    """
    Extract tool-call parameters for a given intent from the user's message.

    Args:
        user_message: raw user text
        intent: the detected intent (must be a key in INTENT_FIELDS)

    Returns:
        dict of field_name -> extracted value (or "unknown" if not found)
    """
    if intent not in INTENT_FIELDS:
        return {}

    fields = INTENT_FIELDS[intent]
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
    prompt = ChatPromptTemplate.from_template(EXTRACTION_PROMPT)
    chain = prompt | llm

    response = chain.invoke({
        "fields": ", ".join(fields),
        "user_message": user_message,
    })

    raw_content = response.content
    if isinstance(raw_content, list):
        # Gemini sometimes returns content as a list of parts; join any text parts
        raw_text = "".join(
            part if isinstance(part, str) else part.get("text", "")
            for part in raw_content
        ).strip()
    else:
        raw_text = raw_content.strip()
    # Strip markdown code fences if the model added them anyway
    raw_text = re.sub(r"^```(json)?|```$", "", raw_text.strip()).strip()

    try:
        extracted = json.loads(raw_text)
    except json.JSONDecodeError:
        # Fallback: return all fields as unknown rather than crashing
        extracted = {field: "unknown" for field in fields}

    # Ensure all expected fields are present even if the LLM missed one
    for field in fields:
        extracted.setdefault(field, "unknown")

    return extracted


if __name__ == "__main__":
    test_cases = [
        ("book_appointment", "I want to book an appointment with cardiology for John Doe on 10th August 2026"),
        ("cancel_appointment", "Please cancel appointment APT-745D38"),
        ("request_refill", "I need a refill for Metformin, my patient ID is PID-9981"),
        ("find_doctor", "Find a doctor for dermatology"),
    ]

    for intent, msg in test_cases:
        result = extract_entities(msg, intent)
        print(f"Intent: {intent}")
        print(f"Message: '{msg}'")
        print(f"Extracted: {result}\n")
