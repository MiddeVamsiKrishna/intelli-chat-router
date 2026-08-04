"""
app.py

Main FastAPI application for the Healthcare Support Chatbot.

Flow for each incoming message:
1. Detect intent using the hybrid router (rule-based -> LLM fallback)
2. If intent == "faq" -> answer via RAG (rag/retriever.py)
3. If intent == "unknown" -> friendly fallback response
4. Otherwise -> extract entities, call the matching tool function

Run locally with:
    uvicorn app:app --reload
Then visit http://127.0.0.1:8000/docs for the interactive API tester.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from intent.router import detect_intent
from intent.extractor import extract_entities
from tools.tools import TOOL_REGISTRY
from rag.retriever import answer_faq

app = FastAPI(
    title="Healthcare Support Chatbot API",
    description="AI chatbot with intelligent tool selection for a healthcare helpdesk domain.",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    user_message: str
    detected_intent: str
    confidence: float
    method: str
    response: str


@app.get("/")
def root():
    return {"status": "ok", "message": "Healthcare Support Chatbot API is running."}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    user_message = request.message

    # Step 1: detect intent
    intent_result = detect_intent(user_message)
    intent = intent_result["intent"]
    confidence = intent_result["confidence"]
    method = intent_result["method"]

    # Step 2: FAQ -> RAG
    if intent == "faq":
        rag_result = answer_faq(user_message)
        return ChatResponse(
            user_message=user_message,
            detected_intent=intent,
            confidence=confidence,
            method=method,
            response=rag_result["message"],
        )

    # Step 3: unknown -> friendly fallback, no tool/RAG call
    if intent == "unknown":
        return ChatResponse(
            user_message=user_message,
            detected_intent=intent,
            confidence=confidence,
            method=method,
            response=(
                "Hi! I'm the healthcare support assistant. I can help you book or "
                "cancel appointments, check appointment status, request prescription "
                "refills, find a doctor, or answer general questions. How can I help?"
            ),
        )

    # Step 4: known actionable intent -> extract entities, call the tool
    entities = extract_entities(user_message, intent)
    tool_function = TOOL_REGISTRY.get(intent)

    if tool_function is None:
        response_text = "Sorry, I understood your request but couldn't find a matching action."
    else:
        tool_result = tool_function(**entities)
        response_text = tool_result["message"]

    return ChatResponse(
        user_message=user_message,
        detected_intent=intent,
        confidence=confidence,
        method=method,
        response=response_text,
    )
