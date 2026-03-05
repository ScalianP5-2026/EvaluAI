# EvaluAI Chatbot Core

Pure chatbot logic without database or API dependencies. Integrates with RAG system (Comp2) and frontend (Comp3).

## 📋 Overview

The Chatbot Core is a standalone module that handles:

- **Prompt Building**: Constructs structured prompts that force JSON-only responses
- **Gemini Integration**: Async communication with Google Gemini 2.5 Flash with retry logic
- **Conversation Memory**: Tracks turns and extracts metadata using heuristics
- **Response Parsing**: Validates JSON responses with automatic fallback

## 🏗️ Architecture

```
chatbot/
├── gemini_client.py       # Google Gemini API async wrapper
├── prompt_builder.py      # Prompt construction with RAG context injection
├── conversation.py        # Conversation tracking and metadata extraction
├── response_parser.py     # JSON validation and fallback handling
└── chatbot_example.py     # Integration example
```

## 🚀 Quick Start

### 1. Initialize Components

```python
from backend.app.chatbot import (
    GeminiChatClient,
    PromptBuilder,
    ConversationMemory,
    parse_response,
)

client = GeminiChatClient(api_key="your-gemini-key")
builder = PromptBuilder()
memory = ConversationMemory(employee_id="EMP_001")
```

### 2. Build and Send Prompt

```python
# Get employee and RAG context
user_context = {
    "department": "Engineering",
    "motivation": 7.5,
    "self_efficacy": 8.0,
}

rag_context = {
    "similar_profiles_summary": "...",
    "department_insights": "...",
    "top_courses": [...],
    "avg_improvement": 25,
}

# Build prompt
prompt = builder.build_contextual_prompt(
    user_message="I want to learn ML",
    user_context=user_context,
    rag_context=rag_context,
    history=memory.get_last_n_turns(n=8),
)

# Send to Gemini
response_text = await client.query(prompt, memory.get_last_n_turns(n=8))
```

### 3. Parse Response

```python
parsed = parse_response(response_text)

print(parsed["message"])  # Conversational response
print(parsed["recommendations"]["course"])  # Recommended course
print(parsed["metadata"]["goal_detected"])  # If goal was detected
```

### 4. Save Metadata

```python
memory.add_turn("assistant", response_text)
metadata = memory.extract_metadata()

# Send to Comp2 for database storage
db.save_metadata(metadata)
```

## 📦 Components

### GeminiChatClient

Async wrapper for Google Gemini 2.5 Flash API.

**Config:**
- Model: `gemini-2.5-flash`
- Temperature: `0.4` (consistency)
- Max tokens: `800` (concise responses)
- Retries: `3` attempts
- Timeout: `30` seconds

**Usage:**
```python
client = GeminiChatClient(api_key="key")
response = await client.query(prompt, history=[])
```

**Errors:**
- `ValueError`: Empty API key or prompt
- `RuntimeError`: All retries failed (timeout/API error)

### PromptBuilder

Constructs prompts that **force JSON-only responses**.

**Methods:**

```python
# Initial consultation (no history)
prompt = builder.build_initial_prompt(user_context)

# Subsequent turns (with RAG context)
prompt = builder.build_contextual_prompt(
    user_message,
    user_context,
    rag_context,  # Can be None (uses defaults)
    history,      # Conversation history
)

# Validate prompt includes JSON instruction
is_valid = builder.validate_prompt_includes_json_instruction(prompt)
```

**Key Features:**
- Explicit "Respond ONLY in JSON" instruction
- RAG context injection (similar profiles, department insights, courses)
- Conversation history included (last 5 turns shown)
- Mandatory JSON structure specification

### ConversationMemory

Tracks conversation and extracts metadata without AI.

**Methods:**

```python
memory = ConversationMemory(employee_id)

# Add turns
memory.add_turn("user", "Learn Python")
memory.add_turn("assistant", "Great choice...")

# Get history (for API calls)
history = memory.get_last_n_turns(n=8)  # Last 8 turns

# Extract metadata (heuristics-based)
metadata = memory.extract_metadata()
# Returns:
# {
#   "conversation_depth": 3,
#   "goal_detected": True,
#   "primary_goal": "Learn Python",
#   "goal_clarity": "high",  # high|medium|low
#   "detected_skills": ["Python"],
#   "has_recommendation": True,
# }

# Serialize/deserialize
data = memory.to_dict()
new_memory = ConversationMemory.from_dict(data)
```

**Goal Detection:**
- **High Clarity**: Verb (want to/need to) + Skill detected
- **Medium Clarity**: Skill only
- **Low Clarity**: No goal or skill

**Limits:**
- Stores max 10 turns
- Sends max 8 turns to API (token limit awareness)

### ResponseParser

Parses responses and handles malformed JSON.

**Strategy:**
1. Try direct JSON parsing
2. Extract JSON block from text
3. Fallback if both fail

**Usage:**
```python
parsed = parse_response(raw_response)

# All responses have this structure:
{
    "success": True/False,
    "message": "...",
    "recommendations": {
        "course": "...",
        "mentor": "...",
        "plan_30_days": [...]
    },
    "insights": {
        "general": "...",
        "department": "...",
        "personal": "..."
    },
    "metadata": {
        "goal_detected": bool,
        "goal_clarity": "high|medium|low",
        "recommended_skill": "..."
    },
    "risk_alert": None or "risk_type",
    "raw": "original response"
}
```

## ✅ JSON Response Structure

Gemini **must** respond in this format:

```json
{
  "message": "Natural conversational response",
  "recommendations": {
    "course": "Course Name",
    "mentor": "Role/Profile",
    "plan_30_days": [
      "Week 1: action",
      "Week 2: action",
      "Week 3: action",
      "Week 4: action"
    ]
  },
  "insights": {
    "general": "Aggregated insight",
    "department": "Dept-specific insight",
    "personal": "Profile-specific insight"
  },
  "metadata": {
    "goal_detected": true,
    "goal_clarity": "high",
    "recommended_skill": "Machine Learning"
  },
  "risk_alert": null
}
```

## 🧪 Testing

### Run All Tests
```bash
pytest backend/tests/chatbot/
```

### Run Specific Test
```bash
pytest backend/tests/chatbot/test_prompt_builder.py -v
```

### Test Coverage
```bash
pytest backend/tests/chatbot/ --cov=backend.app.chatbot
```

### Tests Include:
- **test_prompt_builder.py**: Prompt construction, JSON instruction validation
- **test_response_parser.py**: JSON parsing, fallback handling, structure validation
- **test_conversation.py**: Memory management, goal detection, metadata extraction
- **test_gemini_client.py**: Async queries, retries, timeout handling (with mocks)

## 🔌 Integration with Comp2

**Comp2 provides:**
- SQL-enriched RAG context (similar profiles, dept insights, top courses)
- Employee context from database
- Conversation history from previous turns

**Comp2 receives:**
- Parsed chatbot responses
- Extracted metadata (goals, skills, clarity)
- Serialized conversations for storage

**Example Comp2 usage:**
```python
# In Comp2 (kpi_engine.py or similar)
from backend.app.chatbot import GeminiChatClient, PromptBuilder

# Get contexts
user_context = db.get_employee(employee_id)
rag_context = get_rag_context(employee_id)  # Your SQL enrichment

# Query chatbot
response = await chatbot.client.query(prompt, history)
parsed = parse_response(response)

# Save metadata for KPI calculations
db.save(parsed["metadata"])
```

## 📝 Logging

All components use `logging` module:

```python
import logging
logger = logging.getLogger(__name__)

# Component loggers
# - gemini_client: INFO (queries), WARNING/ERROR (retries, timeouts)
# - prompt_builder: DEBUG (prompt generation)
# - conversation: DEBUG (turns added), INFO (conversation cleared)
# - response_parser: WARNING (parse failures), INFO (successful parses)
```

Configure logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🚨 Error Handling

| Component | Error | Recovery |
|-----------|-------|----------|
| GeminiChatClient | Timeout | Retry 3 times |
| GeminiChatClient | API Error | Retry 3 times |
| GeminiChatClient | API key invalid | ValueError raised |
| ResponseParser | Invalid JSON | Extract JSON block |
| ResponseParser | No JSON found | Return fallback structure |
| ConversationMemory | Max turns exceeded | Remove oldest turn |

## 🔮 Future Enhancements

These are placeholders for v2:

```python
# RAG Vectorial v2
async def generate_embedding(text: str) -> List[float]:
    """Will integrate vector embeddings for semantic search."""
    raise NotImplementedError("Coming in RAG v2")

# Enhanced sentiment analysis
def extract_sentiment(text: str) -> float:
    """Will analyze employee sentiment in conversations."""
    # -1.0 (negative) to 1.0 (positive)

# Complex goal extraction
def extract_complex_goal(text: str) -> Dict:
    """Multi-step goal detection with dependencies."""
```

## 📋 Dependencies

```
google-generativeai==0.3.0
pytest==7.4.3
pytest-asyncio==0.21.1
```

## 🎯 Design Principles

1. **Pure Logic**: No database access, no API routes
2. **Deterministic**: Same input → same output
3. **Testable**: All functions unit testable with mocks
4. **Fallback Safe**: Graceful degradation if JSON parsing fails
5. **MVP First**: Simplicity over feature richness
6. **Future Proof**: Easy to extend for v2 enhancements

## 📞 Contact

**Component Owner:** (Comp1 - Chatbot Core)
**Integrates with:** Comp2 (RAG/KPI), Comp3 (Frontend)
**Status:** Feature-complete MVP
**Deadline Met:** 2 days

---

**Created:** March 5, 2026
**Branch:** feature/chatbot-core
**Last Updated:** March 5, 2026
