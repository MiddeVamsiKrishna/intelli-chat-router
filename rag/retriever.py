"""
rag/retriever.py

RAG (Retrieval Augmented Generation) system for answering FAQ questions.
Instead of exact keyword matching, this embeds the FAQ dataset into a
vector store (FAISS) so questions get matched by MEANING, not exact words.

E.g. "how much does a visit cost" should still retrieve the billing FAQ
even though it doesn't share exact words with "How can I pay my bill?"

Requires: GOOGLE_API_KEY in .env (same key used for intent/llm_based.py)
"""

import os
import json
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

load_dotenv()

RAG_DIR = os.path.dirname(__file__)
FAQ_DATASET_PATH = os.path.join(RAG_DIR, "faq_dataset.json")
VECTOR_STORE_PATH = os.path.join(RAG_DIR, "faq_vector_store")


def _get_embeddings():
    return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def build_vector_store():
    """
    Builds the FAISS vector store from faq_dataset.json and saves it to disk.
    Run this once (or whenever the FAQ dataset changes) — NOT on every request,
    since embedding calls cost time/quota.
    """
    with open(FAQ_DATASET_PATH, "r") as f:
        faq_data = json.load(f)

    documents = [
        Document(
            page_content=item["question"],
            metadata={"answer": item["answer"]},
        )
        for item in faq_data
    ]

    embeddings = _get_embeddings()
    vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local(VECTOR_STORE_PATH)
    print(f"Vector store built and saved to {VECTOR_STORE_PATH} ({len(documents)} FAQ entries)")
    return vector_store


def load_vector_store():
    """Loads the previously-built vector store from disk."""
    if not os.path.exists(VECTOR_STORE_PATH):
        print("Vector store not found — building it now...")
        return build_vector_store()

    embeddings = _get_embeddings()
    return FAISS.load_local(
        VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True
    )


def answer_faq(user_question: str, k: int = 1) -> dict:
    """
    Retrieve the best-matching FAQ answer for a user's question.

    Args:
        user_question: the user's raw question
        k: how many top matches to retrieve (default 1 — just the best match)

    Returns:
        dict with status, message (the answer), and matched_question (for debugging)
    """
    vector_store = load_vector_store()
    results = vector_store.similarity_search(user_question, k=k)

    if not results:
        return {
            "status": "not_found",
            "tool": "faq_rag",
            "message": "I couldn't find an answer to that in our FAQ. Let me escalate this to a human.",
        }

    best_match = results[0]
    return {
        "status": "success",
        "tool": "faq_rag",
        "matched_question": best_match.page_content,
        "message": best_match.metadata["answer"],
    }


if __name__ == "__main__":
    # First run builds the vector store; subsequent runs reuse it.
    test_questions = [
        "What time can I visit patients?",       # rephrased "visiting hours"
        "How much does it cost to see a doctor?",  # rephrased "billing"
        "Where can I park my car?",                # rephrased "parking"
        "Does the chatbot diagnose illnesses?",     # rephrased medical-advice FAQ
    ]

    for q in test_questions:
        result = answer_faq(q)
        print(f"Q: '{q}'")
        print(f"   Matched FAQ: {result.get('matched_question')}")
        print(f"   Answer: {result['message']}\n")
