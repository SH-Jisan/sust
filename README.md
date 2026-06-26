# QueueStorm Investigator — Digital Finance SupportOps Copilot

QueueStorm Investigator is a production-ready, high-performance, and safe AI/API service that serves as an internal copilot for digital finance support teams (e.g., bKash). It analyzes customer ticket text alongside transaction history to investigate claim veracity, assign severity and department routing, and draft safe customer responses that protect user credentials.

---

## 🛠️ Technology Stack
*   **Core Framework**: Python 3.11 with **FastAPI** (asynchronous, high performance, auto-documented routes).
*   **Validation Layer**: **Pydantic v2** (strict type constraints, automated request/response schema parsing).
*   **AI Integration**: Asynchronous HTTPX client supporting **Google Gemini** (Gemini 1.5 Flash) and **OpenAI** (GPT-4o-mini).
*   **Test Suite**: **pytest** (unit, security, and integration test coverage).
*   **Containerization**: **Docker** (slim Python Multi-stage base image).

---

## 🚀 Setup & Execution Instructions

### Local Setup
1. Clone the repository and navigate to the project directory:
   ```bash
   cd sust
   ```
2. Initialize and activate a virtual environment:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   Copy `.env.example` to `.env` and fill in your keys:
   ```bash
   cp .env.example .env
   ```

### Running the API Server
Start the local server using Uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
*   **Health check**: `http://localhost:8000/health`
*   **Analyze Route**: `http://localhost:8000/analyze-ticket`
*   **Interactive API Docs (Swagger)**: `http://localhost:8000/docs`

### Running the Test Suite
Execute end-to-end integration and safety tests:
```bash
python -m pytest tests/
```

### Docker Execution
1. Build the lightweight container image (aims for < 500MB):
   ```bash
   docker build -t queuestorm-team .
   ```
2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env queuestorm-team
   ```

---

## 🏗️ Technical Architecture & AI Approach
The application employs a **Hybrid Rule + AI Architecture** that maximizes reliability and security while minimizing latency:

1.  **Deterministic Engine First**: When a ticket is received, a Python-based rule engine checks the transaction log to evaluate amounts and timestamps. It programmatically resolves `evidence_verdict`, `relevant_transaction_id`, and `human_review_required`.
2.  **AI Text Generation**: The resolved metadata is sent to the LLM (Gemini 1.5 Flash or GPT-4o-mini) alongside the ticket complaint. The LLM handles natural language tasks: summarizing the complaint (`agent_summary`), proposing the next action (`recommended_next_action`), and drafting the response (`customer_reply`).
3.  **Safety Guardrail Interceptor (Post-Processor)**: Before returning the response, a regex-based interceptor parses the text to catch and rewrite any credential requests, unauthorized refund promises, or suspicious third-party links.

---

## 🛡️ Safety Logic & Guardrails
*   **Phishing Mitigation**: Regex blocks look for patterns asking for PIN, OTP, password, or card numbers in replies. If found, the filter intercepts and overwires the text with a strict security warning.
*   **Refund Protection**: Automatically replaces absolute confirmations (e.g. "We will refund you") with compliant language: "any eligible amount will be returned through official channels".
*   **Prompt Injection Protection**: Complaints are isolated inside XML tags within the LLM prompt. The system instructions declare that anything inside these tags must not be executed as instructions.

---

## 🤖 MODELS Section
| Model | Type / Run location | Rationale for Choice |
| :--- | :--- | :--- |
| **Gemini 1.5 Flash** | Cloud API (Google AI) | Chosen as the primary model. Extremely cost-effective, possesses native multilingual understanding (excellent for Bangla/Banglish), and offers low API latency. |
| **GPT-4o-mini** | Cloud API (OpenAI) | Secondary fallback model. High instruction adherence for structured JSON outputs and competitive pricing. |
| **Template Fallback Engine** | Local Python Engine | Triggered if API keys are missing or rate-limited. Guarantees 0ms latency, high reliability, and schema correctness. |

---

## 📝 Assumptions & Limitations
*   **ISO 8601 Datetime Proximity**: It is assumed that when users mention "yesterday" or "today", it is evaluated relative to the timestamp of the latest transaction in the payload.
*   **Transaction Matching Bounds**: programmatically flags duplicate payments if two completed payment transactions to the same merchant match the amount and occur within 10 minutes (600 seconds) of each other.
*   **External API Availability**: Requires outbound internet access to Google AI or OpenAI endpoints. If blocked, the service falls back to the static template engine.
