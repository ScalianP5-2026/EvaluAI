"""
EvaluAI Chatbot Core - Integration Example

This file demonstrates how to use the Chatbot Core components together.
It shows the complete workflow from initialization through conversation and response parsing.

NOTE: This is for documentation/testing purposes with mocked Gemini calls.
"""

import asyncio
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import chatbot core components
from backend.app.chatbot.gemini_client import GeminiChatClient
from backend.app.chatbot.prompt_builder import PromptBuilder
from backend.app.chatbot.conversation import ConversationMemory
from backend.app.chatbot.response_parser import parse_response


async def example_chatbot_interaction():
    """
    Example of a complete chatbot interaction flow.
    
    Steps:
    1. Initialize components
    2. Get user context and RAG context
    3. Build prompts
    4. Send to Gemini
    5. Parse response
    6. Save metadata
    """

    # ==================== 1. INITIALIZE COMPONENTS ====================
    print("\n=== INITIALIZING CHATBOT CORE ===")
    
    # NOTE: In production, get API_KEY from environment
    API_KEY = "your-actual-gemini-api-key-here"
    
    # Initialize components
    client = GeminiChatClient(api_key=API_KEY)
    builder = PromptBuilder()
    memory = ConversationMemory(employee_id="EMP_12345")
    
    print("✓ GeminiChatClient initialized")
    print("✓ PromptBuilder initialized")
    print("✓ ConversationMemory initialized")

    # ==================== 2. PREPARE CONTEXT ====================
    print("\n=== PREPARING CONTEXT ===")
    
    # Employee context (comes from frontend/Comp2)
    user_context = {
        "employee_id": "EMP_12345",
        "department": "Engineering",
        "education_level": "Master",
        "ai_usage_frequency": 4,
        "motivation": 7.5,
        "self_efficacy": 8.0,
        "seniority": "Senior Engineer",
    }
    
    # RAG context (comes from SQL query via Comp2)
    rag_context = {
        "similar_profiles_summary": (
            "25 senior engineers in similar roles improved their ML skills "
            "by 32% on average within 3 months"
        ),
        "department_insights": (
            "Engineering dept prioritizes practical skills. "
            "87% complete hands-on projects, 65% pursue certifications"
        ),
        "top_courses": [
            {"title": "ML Systems Design", "completion_rate": 0.92},
            {"title": "Advanced Python", "completion_rate": 0.88},
            {"title": "Product ML", "completion_rate": 0.81},
        ],
        "avg_improvement": 32,
        "risk_flags": [],
    }
    
    print("✓ User context loaded")
    print("✓ RAG context loaded from SQL")

    # ==================== 3. FIRST TURN: INITIAL CONSULTATION ====================
    print("\n=== FIRST TURN: INITIAL CONSULTATION ===")
    
    # Build initial prompt
    initial_prompt = builder.build_initial_prompt(user_context)
    
    print("✓ Initial prompt built")
    print(f"✓ Prompt length: {len(initial_prompt)} characters")
    print(f"✓ Prompt includes JSON format instruction: "
          f"{builder.validate_prompt_includes_json_instruction(initial_prompt)}")
    
    # Send to Gemini
    try:
        print("\n→ Sending to Gemini API...")
        response_text = await client.query(initial_prompt, history=[])
        
        # Save to memory
        memory.add_turn("assistant", response_text)
        
        # Parse response
        parsed = parse_response(response_text)
        
        print("✓ Response received and parsed")
        print(f"✓ Parsed successfully: {parsed['success']}")
        print(f"✓ Message: {parsed['message'][:100]}...")
        
        # Extract metadata after first turn
        metadata = memory.extract_metadata()
        print(f"✓ Metadata: {metadata}")
        
    except RuntimeError as e:
        print(f"✗ Error from Gemini: {e}")
        print("  (In production, this would retry or fallback)")
        return

    # ==================== 4. SECOND TURN: USER FOLLOW-UP ====================
    print("\n=== SECOND TURN: USER FOLLOW-UP ===")
    
    # User sends follow-up message
    user_message = "The ML Systems Design course sounds great. What's the time commitment?"
    
    print(f"User: {user_message}")
    
    # Add to memory
    memory.add_turn("user", user_message)
    
    # Build contextual prompt with full context
    contextual_prompt = builder.build_contextual_prompt(
        user_message=user_message,
        user_context=user_context,
        rag_context=rag_context,
        history=memory.get_last_n_turns(n=8),  # Send last 8 turns (API limit aware)
    )
    
    print("✓ Contextual prompt built with RAG enrichment")
    print(f"✓ Includes conversation history: {len(memory.get_history())} turns")
    
    try:
        # Send contextual query
        print("\n→ Sending contextual query to Gemini...")
        response_text = await client.query(
            contextual_prompt,
            history=memory.get_last_n_turns(n=8)
        )
        
        # Save to memory
        memory.add_turn("assistant", response_text)
        
        # Parse response
        parsed = parse_response(response_text)
        
        print("✓ Response received and parsed")
        print(f"✓ Recommendations: {parsed['recommendations'].get('course', 'N/A')}")
        
        # Extract final metadata
        metadata = memory.extract_metadata()
        print(f"✓ Goal detected: {metadata['goal_detected']}")
        print(f"✓ Goal clarity: {metadata['goal_clarity']}")
        print(f"✓ Detected skills: {metadata['detected_skills']}")
        
    except RuntimeError as e:
        print(f"✗ Error from Gemini: {e}")
        return

    # ==================== 5. SAVE SESSION METADATA ====================
    print("\n=== SAVING SESSION METADATA ===")
    
    # Serialize conversation for persistence
    conversation_data = memory.to_dict()
    
    # In production, this would be sent to Comp2 for BD storage
    print("✓ Conversation serialized")
    print(f"  - Employee: {conversation_data['employee_id']}")
    print(f"  - Turns: {len(conversation_data['turns'])}")
    print(f"  - Metadata: {conversation_data['metadata']}")
    
    # ==================== 6. SUMMARY ====================
    print("\n=== CHATBOT CORE WORKFLOW COMPLETE ===")
    print("\nWhat happened:")
    print("1. ✓ Initialized all components (client, builder, memory)")
    print("2. ✓ Built initial prompt with employee context")
    print("3. ✓ Sent to Gemini, got JSON response")
    print("4. ✓ Parsed response and extracted insights")
    print("5. ✓ Handled follow-up with RAG enriched context")
    print("6. ✓ Saved conversation and metadata for persistence")
    print("\nNext steps:")
    print("- Comp2 saves metadata to database")
    print("- Frontend displays response to user")
    print("- System calculates KPIs and tracks engagement")


# ==================== USAGE ====================

if __name__ == "__main__":
    """
    Run the example (requires valid Gemini API key).
    
    Usage:
        python backend/app/chatbot/chatbot_example.py
    """
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║         EvaluAI Chatbot Core - Integration Example             ║
    ║                                                                 ║
    ║ This example demonstrates the complete chatbot workflow:       ║
    ║ • Component initialization                                     ║
    ║ • Prompt building (initial + contextual)                       ║
    ║ • Gemini API communication                                     ║
    ║ • Response parsing and validation                              ║
    ║ • Metadata extraction                                          ║
    ║ • Session persistence                                          ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    print("\nNOTE: This example requires a valid Gemini API key.")
    print("Set your API key in the code or use environment variable:\n")
    print("  export GEMINI_API_KEY='your-key-here'")
    print("  python chatbot_example.py\n")
    
    try:
        asyncio.run(example_chatbot_interaction())
    except Exception as e:
        logger.error(f"Example failed: {e}")
        print(f"\n✗ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Valid Gemini API key")
        print("  2. google-generativeai package installed")
        print("  3. All dependencies in requirements.txt installed")


# ==================== COMPONENT CONTRACT ====================

"""
CONTRACT WITH COMP2 (RAG/SQL Manager):

Comp2 calls the chatbot core like this:

from backend.app.chatbot import (
    GeminiChatClient,
    PromptBuilder,
    ConversationMemory,
    parse_response,
)

# Initialize
client = GeminiChatClient(api_key=os.getenv("GEMINI_API_KEY"))
builder = PromptBuilder()
memory = ConversationMemory(employee_id)

# Get contexts from your database
user_context = db.get_employee_context(employee_id)
rag_context = db.get_rag_context(employee_id)  # SQL-enriched

# Build prompt and query
if first_turn:
    prompt = builder.build_initial_prompt(user_context)
else:
    prompt = builder.build_contextual_prompt(
        user_message=message,
        user_context=user_context,
        rag_context=rag_context,
        history=memory.get_last_n_turns(n=8),
    )

response_text = await client.query(prompt, memory.get_last_n_turns(n=8))
parsed = parse_response(response_text)

# Save results
memory.add_turn("assistant", response_text)
metadata = memory.extract_metadata()

# Comp2 saves metadata to database
db.save_session_metadata(metadata)
db.save_conversation(memory.to_dict())


RESPONSE GUARANTEES:

✓ Always returns valid JSON structure
✓ parse_response() handles malformed JSON gracefully
✓ ConversationMemory caps at 10 turns, sends 8 to API
✓ Temperature 0.4 ensures consistency
✓ 3 retries with 30s timeout per request
✓ All errors logged for debugging
"""
