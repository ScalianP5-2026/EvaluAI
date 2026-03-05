"""
Configuration for EvaluAI Chatbot Core.

Centralized configuration for all chatbot parameters.
Easy to modify without changing component code.
"""

# ==================== GEMINI API CONFIG ====================
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TEMPERATURE = 0.4  # For consistency (0.0-1.0)
GEMINI_MAX_TOKENS = 800  # For concise responses
GEMINI_TIMEOUT_SECONDS = 30  # Request timeout
GEMINI_MAX_RETRIES = 3  # Retry attempts on failure

# ==================== CONVERSATION MEMORY ====================
CONVERSATION_MAX_TURNS = 10  # Max turns stored in memory
CONVERSATION_MAX_TURNS_TO_API = 8  # Max turns sent to Gemini API

# ==================== GOAL DETECTION ====================
# Keywords to detect learning/training intent
GOAL_DETECTION_KEYWORDS = [
    "learn",
    "improve",
    "develop",
    "advance",
    "study",
    "train",
    "certification",
    "master",
    "become",
]

# Goal clarity calculation
GOAL_CLARITY_LEVELS = {
    "high": "Verb (want to/need to) + Skill detected",
    "medium": "Skill only",
    "low": "No goal or skill detected",
}

# Verbs that indicate clear intent
CLEAR_INTENT_VERBS = ["want to", "need to", "must", "should"]

# ==================== SKILL DETECTION ====================
# Regex patterns for skill detection
SKILL_PATTERNS = [
    r"\b(python|java|javascript|ml|machine learning|ai|artificial intelligence)\b",
    r"\b(data science|data analysis|analytics)\b",
    r"\b(cloud|aws|azure|gcp)\b",
    r"\b(leadership|management|communication)\b",
    r"\b(agile|scrum|devops)\b",
    r"\b(sql|database|backend|frontend)\b",
]

# ==================== LOGGING ====================
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ==================== RESPONSE PARSING ====================
# Required fields in parsed response
RESPONSE_REQUIRED_FIELDS = [
    "success",
    "message",
    "recommendations",
    "insights",
    "raw",
]

# ==================== PROMPT INSTRUCTIONS ====================
# Mandatory instruction for JSON-only responses
JSON_ONLY_INSTRUCTION = (
    "You MUST respond ONLY with this exact JSON structure (no other text):"
)

# System role for all prompts
SYSTEM_ROLE = (
    "You are an expert in corporate training and AI-based learning.\n"
    "Your goal is to help employees improve their learning journey.\n"
    "You MUST respond ALWAYS in valid JSON format.\n"
    "Do NOT include any text outside the JSON.\n"
    "If you deviate from the JSON format, the system will reject your response.\n"
    "No markdown, no explanations, no preamble."
)

# ==================== DEFAULTS & FALLBACKS ====================
DEFAULT_USER_CONTEXT_FIELDS = {
    "department": "Unknown",
    "motivation": 5,
    "self_efficacy": 5,
    "ai_usage_frequency": 3,
    "seniority": "Mid-level",
    "education_level": "Bachelor",
}

DEFAULT_RAG_CONTEXT = {
    "similar_profiles_summary": "No similar profiles analyzed yet",
    "department_insights": "Department data being loaded",
    "top_courses": [],
    "avg_improvement": 0,
    "risk_flags": [],
}

# ==================== FEATURE FLAGS ====================
ENABLE_SENTIMENT_ANALYSIS = False  # Future: v2
ENABLE_VECTORIAL_RAG = False  # Future: v2
ENABLE_COMPLEX_GOAL_DETECTION = False  # Future: v2

# ==================== DEBUG ====================
DEBUG_MODE = False  # Set to True for extra logging
PRESERVE_RAW_RESPONSE = True  # Keep original response for debugging
