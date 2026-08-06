# Healthcare Support Chatbot — Intelligent Tool Selection

An AI chatbot for a Healthcare Support helpdesk that automatically detects user intent
and selects the correct tool (book/cancel appointments, check status, request refills,
find a doctor) or answers FAQ questions using RAG. Built for Problem Statement 1:
"AI Chatbot with Intelligent Tool Selection."

## Features

- **Hybrid intent detection** — fast rule-based keyword matching, with an LLM (Google Gemini)
  fallback for natural/ambiguous phrasing
- **Real tool execution** — appointments, refills, and escalations persist to local JSON files
- **RAG-based FAQ answering** — semantic search over a FAQ dataset using FAISS + Gemini embeddings
- **Safety guardrail** — automatically escalates medical/symptom questions to a human instead
  of giving medical advice
- **FastAPI backend** — a single `/chat` endpoint ties everything together
- **Web chat interface** — a lightweight HTML/CSS/JS front end (`chat_ui.html`) for interacting
  with the chatbot conversationally, instead of using the raw API docs

## Project Structure

```
intelli-chat-router/
├── intent/
│   ├── rule_based.py      # Keyword-based intent detector
│   ├── llm_based.py       # Gemini-based intent detector
│   ├── router.py          # Hybrid router combining both
│   └── extractor.py       # Extracts tool parameters from user messages
├── tools/
│   ├── tools.py           # Tool functions (book/cancel/refill/find doctor/escalate)
│   └── data/              # Local JSON "database" (auto-created on first run)
├── rag/
│   ├── faq_dataset.json   # FAQ question/answer pairs
│   ├── retriever.py       # Vector store + semantic search over the FAQ
│   └── faq_vector_store/  # Saved FAISS index (auto-created on first run)
├── eval/
│   ├── test_dataset.json  # Evaluation test cases (clear/ambiguous/multi-step/sensitive)
│   └── evaluate.py        # Runs the test dataset and reports accuracy
├── app.py                 # FastAPI application (main entry point)
├── chat_ui.html           # Web chat interface (connects to app.py's /chat endpoint)
├── requirements.txt
├── REPORT.md
└── README.md
```

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/MiddeVamsiKrishna/intelli-chat-router.git
cd intelli-chat-router
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key
Create a `.env` file in the project root with:
```
GOOGLE_API_KEY=your-gemini-api-key-here
```
Get a free key at: https://aistudio.google.com/app/apikey

### 5. Run the application
```bash
uvicorn app:app --reload
```

### 6. Test it
Open your browser to:
```
http://127.0.0.1:8000/docs
```
This opens the interactive Swagger UI where you can test the `/chat` endpoint directly.

Example request:
```json
{
  "message": "I want to book an appointment with cardiology for John Doe on 10th August 2026"
}
```

### 7. (Optional) Use the web chat interface

For a more natural, conversational way to interact with the chatbot instead of the raw
API docs, open `chat_ui.html` directly in your browser (double-click the file, or drag
it into a browser tab) while the FastAPI server from Step 5 is still running. This gives
a real chat-style interface with message bubbles, and shows which detection method
(rule-based or AI-based) handled each response.

## Running the Evaluation

To measure intent detection accuracy across the test dataset:
```bash
python -m eval.evaluate
```
This prints a pass/fail log per test case, plus an overall accuracy summary broken down
by category (clear, ambiguous, multi-step, sensitive) and saves detailed results to
`eval/results.json`.

**Note:** Google's Gemini free tier has a daily request quota. If you hit a `429` quota
error mid-evaluation, this is expected — see REPORT.md for details on this limitation.

## Example Interactions

| User message | Detected intent | Action |
|---|---|---|
| "Cancel my appointment please" | `cancel_appointment` | Cancels the appointment (rule-based) |
| "My meds are running low, can you help?" | `request_refill` | Submits a refill request (LLM fallback) |
| "What are your visiting hours?" | `faq` | Answers from FAQ via RAG |
| "I have chest pain, what should I do?" | `escalate_to_human` | Refuses medical advice, escalates to a human |

## Tech Stack

- Python, FastAPI
- LangChain + Google Gemini (`gemini-flash-latest`)
- FAISS (vector store for RAG)
- Local JSON files as a lightweight mock database

## Author

Vamsi Krishna Midde
