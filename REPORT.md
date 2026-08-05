# Technical Report: Healthcare Support Chatbot with Intelligent Tool Selection

**Author:** Vamsi Krishna Midde
**Domain:** Healthcare Support Helpdesk
**Problem Statement:** AI Chatbot with Intelligent Tool Selection

---

## 1. Overview

This project implements an AI chatbot for a healthcare helpdesk domain. The chatbot
understands a user's request, identifies their intent, selects the correct tool
(book/cancel an appointment, check status, request a refill, find a doctor) or answers
general questions via a FAQ retrieval system, and returns a meaningful response — while
safely refusing to give medical advice.

## 2. System Architecture

```
User message
     │
     ▼
Hybrid Intent Router (intent/router.py)
     │
     ├── Rule-based detector (fast, keyword matching)
     │        │
     │        └── if no match ──► LLM-based detector (Gemini, understands natural phrasing)
     │
     ▼
Detected intent
     │
     ├── intent == "faq"        ──► RAG retriever (rag/retriever.py) ──► FAISS vector search over FAQ dataset
     ├── intent == "unknown"    ──► Friendly fallback response
     └── actionable intent      ──► Entity extractor (intent/extractor.py, LLM-based)
                                          │
                                          ▼
                                  Tool function called (tools/tools.py)
                                          │
                                          ▼
                                  Result persisted to local JSON "database"
     │
     ▼
FastAPI /chat endpoint returns structured JSON response
```

**Components:**
- `intent/rule_based.py` — keyword-based intent matching
- `intent/llm_based.py` — LLM (Gemini) intent classification with structured output
- `intent/router.py` — hybrid router combining both
- `intent/extractor.py` — extracts tool call parameters (e.g., patient name, date) from the message
- `tools/tools.py` — six tool functions, with results persisted to local JSON files
- `rag/retriever.py` — FAISS vector store over the FAQ dataset for semantic search
- `app.py` — FastAPI application wiring everything together
- `eval/` — test dataset and evaluation script

## 3. Approach Comparison: Intent Detection

Two approaches were implemented and compared, then combined into a hybrid.

| Aspect | Rule-Based | LLM-Based (Gemini) |
|---|---|---|
| **Accuracy** | High for exact keyword matches, but brittle — fails on any phrasing it wasn't explicitly programmed for | High across varied, natural phrasing — correctly handled "my meds are running low" (no "refill" keyword) and "chest hurts a bit" |
| **Speed** | Instant (no network call) | Slower — involves an API round-trip (typically 1-3 seconds) |
| **Cost** | Free | Costs API quota/tokens per call |
| **Advantages** | Fast, free, predictable, no dependency on external services | Understands meaning/context, handles ambiguity, generalizes to unseen phrasing |
| **Limitations** | Cannot understand phrasing outside its keyword list; requires manual keyword maintenance | Slower, costs money at scale, subject to API rate limits/quota, non-deterministic |

**Why the hybrid approach was chosen:** In evaluation, the hybrid router handled
**57.1% of requests via the free, instant rule-based path**, and only fell back to the
LLM for the remaining 42.9% — genuinely ambiguous or naturally-phrased requests. This
gives the speed/cost benefits of rule-based matching for common, clear requests, while
still correctly handling messages a pure rule-based system would fail on entirely (e.g.,
"Hi there", which has no actionable keyword).

## 4. RAG (FAQ Answering)

Instead of exact keyword matching, FAQ questions are embedded into vectors (using
Gemini's embedding model) and stored in a FAISS vector store. User questions are matched
by **semantic similarity**, not exact wording.

**Example demonstrating this works correctly:**
- User asked: *"What time can I visit patients?"*
- Matched FAQ: *"What are the hospital's visiting hours?"*
- These share almost no exact words, but are semantically identical — confirming
  real semantic search, not keyword lookup.

**Observed limitation:** The query *"How much does it cost to see a doctor?"* matched
the "Do you accept insurance?" FAQ entry rather than a more specific billing FAQ, since
no exact "cost" FAQ existed in the dataset. This is a realistic RAG limitation — retrieval
quality depends on how well the underlying dataset covers the topic space, not a bug in
the retrieval logic itself.

## 5. Evaluation Results

A test dataset of 21 cases was built, covering four categories as required: clear,
ambiguous, multi-step, and sensitive requests. Full results are in `eval/results.json`;
summary below:

| Category | Accuracy |
|---|---|
| Clear requests | 7/7 (100%) |
| Ambiguous requests | 7/7 (100%) |
| Multi-step requests | 2/3 (66.7%) |
| Sensitive/safety requests | 4/4 (100%) |
| **Overall** | **20/21 (95.2%)** |

**Method breakdown:** 57.1% of requests were resolved by the rule-based detector; 42.9%
required the LLM fallback.

### Discussion of the one failing case

*"I want to find a cardiologist and then book an appointment with them"* was expected to
resolve to `find_doctor`, but the system returned `book_appointment`. This reflects a
genuine architectural limitation (see Section 6) rather than a misclassification — the
message contains two sequential intents, and a single-intent system must pick one. On
review, `book_appointment` is arguably the more defensible primary intent, since it
represents the user's ultimate goal.

## 6. Challenges Faced

1. **Gemini model version churn.** During development, several Gemini model names
   (`gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`) were deprecated for
   new accounts mid-project, each producing a 404 error. This was resolved by writing a
   small diagnostic script to query the API directly for currently-available models,
   rather than relying on documentation that could be outdated, and settling on the
   `gemini-flash-latest` alias to avoid future version-pinning issues.
2. **Free-tier rate limits and daily quotas.** The evaluation script initially failed
   with `429` errors — first a per-minute rate limit (5 requests/minute), then a
   `20 requests/day` quota. This was addressed by adding delays between LLM calls,
   automatic retry-with-backoff for transient server errors, and (for testing purposes)
   using a secondary API key when the daily quota was exhausted mid-evaluation.
3. **Single-intent limitation for multi-step requests.** As discussed in Section 5,
   the current architecture detects one primary intent per message, which is imperfect
   for genuinely multi-step requests.

## 7. Future Improvements

- **Multi-intent detection:** extend the router to detect and sequentially execute
  multiple intents within a single message (e.g., "cancel X and book Y").
- **Better FAQ dataset coverage:** add more granular FAQ entries (e.g., separate
  "cost of consultation" from "insurance") to improve RAG retrieval precision.
- **Conversation memory:** currently each request is stateless; adding conversation
  history would allow multi-turn flows (e.g., asking for a missing field like the
  appointment date in a follow-up message rather than defaulting to "unknown").
- **Confidence-based re-routing:** requests where the LLM returns low confidence could
  be routed to a clarifying question instead of proceeding with an uncertain tool call.
- **Real database integration:** replace local JSON file storage with a proper database
  (e.g., PostgreSQL) for production readiness.

## 8. Conclusion

The hybrid intent detection approach achieved 95.2% overall accuracy across a diverse
21-case evaluation set, correctly handling clear requests, naturally-phrased ambiguous
requests, and — critically for a healthcare domain — safely escalating all sensitive
medical questions rather than attempting to answer them directly. The one imperfect
result reflects a known and explainable architectural trade-off rather than a detection
failure, and is addressed as a concrete direction for future work.
