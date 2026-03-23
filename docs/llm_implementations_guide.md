# EvaluAI Chatbot: LLM Implementations Guide

This document outlines the architecture, technical specifications, and integration details of the two Large Language Model (LLM) options available in the EvaluAI platform: **Google Gemini** and **Azure OpenAI (Foundry)**.

## 1. Overview
The EvaluAI chatbot is designed with a provider-agnostic architecture. The core application logic—including context aggregation, conversation history management, and the `HybridRAGOrchestrator`—is decoupled from the actual LLM API calls. This allows the application to switch seamlessly between models simply by passing a different `provider` variable from the frontend UI.

Both client classes implement the same asynchronous signature:
```python
async def query(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
```
Because they share the exact same interface, the Python backend can route prompts and receive strictly formatted JSON outputs regardless of the underlying LLM.

---

## 2. Google Gemini Implementation

### Technical Specs
*   **Provider:** Google Generative AI
*   **Model:** Gemini 2.5 Flash (`gemini-2.5-flash`)
*   **Client Class:** `GeminiChatClient` (`backend/app/chatbot/gemini_client.py`)
*   **SDK:** `google-genai` (native python library)

### How It Works
1.  **Initialization:** The client is instantiated using the `GEMINI_API_KEY`.
2.  **Prompting:** It receives a heavily crafted system prompt structured by `PromptBuilder`. This prompt explicitly instructs the LLM to output valid JSON.
3.  **Execution:** The chat history and user prompt are passed to the `AsyncGenerateContent` method.
4.  **Benefits:** Gemini 2.5 Flash is highly optimized for speed and cost-effectiveness, making it incredibly fast at parsing RAG context and generating responses.

---

## 3. Azure OpenAI (Foundry) Implementation

### Technical Specs
*   **Provider:** Azure Cognitive Services (Microsoft)
*   **Model:** GPT-4.1-mini (or equivalent deployment)
*   **Client Class:** `FoundryChatClient` (`backend/app/chatbot/foundry_client.py`)
*   **SDK:** Native `httpx.AsyncClient` (direct REST API)

### How It Works
1.  **Initialization:** Connects via a private Azure endpoint (`CHATBOT_FOUNDRY_ENDPOINT`) using an `api-key` header and targeting a specific `deployment` string.
2.  **Structured JSON Outputs:** Unlike the Gemini SDK which relies on prompt engineering to enforce JSON, the Foundry client uses **Strict JSON Schemas** (`response_format: {"type": "json_schema"}`).
    *   This forces the Azure endpoint engine to strictly bind all tokens to the expected JSON structure (ensuring fields like `message`, `recommendations`, `insights` are definitively present).
3.  **Resilience:** The client includes built-in retry logic (`max_retries`) and timeout fallbacks. If the strict schema is rejected by Azure due to hallucination bounds, it gracefully retries without it.
4.  **Prompt Restraints:** Because strict schemas enforce fields to exist, `PromptBuilder` provides explicit instructions to the model to fill optional fields (like `plan_30_days`) with `null` automatically, preventing it from hallucinating a 30-day plan every time the user speaks.

---

## 4. Frontend & Backend Interactions

### Frontend Provider Switch (`ChatPage.jsx`)
The frontend contains a React state `provider` hooked up to a UI toggle button. When the user sends a message:
```javascript
const response = await chatAPI.sendMessage(userId, message, provider); // "gemini" or "foundry"
```

### Backend Resolution (`chat_routes.py`)
In the main `/chat/query` FastAPI endpoint, the backend checks the provider type injected from the payload.
```python
if request.provider.lower() in ("foundry", "azure", "azure_openai"):
    client = FoundryChatClient()
else:
    client = GeminiChatClient(api_key=GEMINI_API_KEY)

# The client is then passed into standard business logic seamlessly:
response_text = await client.query(prompt=contextual_prompt, history=chat_history)
```

## 5. Environment Strategy
To configure the services, the following `.env` variables are pivotal:

**Gemini Requirements:**
*   `GEMINI_API_KEY="AIzaSy..."`

**Azure Foundry Requirements:**
*   `CHATBOT_FOUNDRY_ENDPOINT="https://<resource-name>.openai.azure.com"`
*   `CHATBOT_FOUNDRY_API_KEY="<azure-key>"`
*   `CHATBOT_FOUNDRY_DEPLOYMENT="<deployment-name>"`
*   `CHATBOT_FOUNDRY_API_VERSION="2024-02-15-preview"`
