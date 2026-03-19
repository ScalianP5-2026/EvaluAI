"""
PromptBuilder for EvaluAI Chatbot Core.

Constructs structured prompts to ensure Gemini 2.5 Flash responds in JSON format.
The goal is to force deterministic, parseable JSON output from the LLM.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from . import settings

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Builds structured prompts for Gemini 2.5 Flash.
    
    CRITICAL: Forces JSON-only output to enable automatic parsing.
    All prompts must include strict JSON format instructions.
    
    Goal detection keywords loaded from environment variable CHATBOT_GOAL_DETECTION_KEYWORDS
    """

    def __init__(self):
        """Initialize PromptBuilder with system role."""
        self.system_role = (
            "You are an expert in corporate training and AI-based learning.\n"
            "Your goal is to help employees improve their learning journey.\n"
            "You MUST respond ALWAYS in valid JSON format.\n"
            "Do NOT include any text outside the JSON.\n"
            "If you deviate from the JSON format, the system will reject your response.\n"
            "No markdown, no explanations, no preamble."
        )

    @staticmethod
    def _resolve_ai_usage_frequency(user_context: Dict[str, Any]) -> Any:
        """Use canonical AI usage key, with backward-compatible fallback."""
        return user_context.get(
            "ai_usage_frequency",
            user_context.get("ai_usage", 3),
        )

    @staticmethod
    def _resolve_seniority(user_context: Dict[str, Any]) -> str:
        """Resolve seniority from context, deriving it from years if missing."""
        explicit = user_context.get("seniority")
        if explicit:
            return str(explicit)

        years = user_context.get("years_in_company")
        try:
            years_value = float(years)
        except (TypeError, ValueError):
            return "Mid-level"

        if years_value < 2:
            return "Junior"
        if years_value < 6:
            return "Mid-level"
        return "Senior"

    @staticmethod
    def _build_retrieved_facts_block(user_context: Dict[str, Any]) -> str:
        """
        Serialize compact retrieved facts for prompt injection.
        """
        facts = user_context.get("retrieved_facts", {})
        if not facts:
            return "No retrieved facts available."
        try:
            return json.dumps(facts, ensure_ascii=False)
        except Exception:
            return str(facts)

    def build_initial_prompt(
        self, 
        user_context: Dict[str, Any],
        ml_scores: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build initial prompt before conversation history exists.

        Args:
            user_context: Employee context dict with keys:
                - department (str)
                - motivation (float, 1-7)
                - self_efficacy (float, 1-7)
                - ai_usage (int, 1-5)
                - seniority (str)
                - education_level (str)

        Returns:
            Formatted prompt string ready for Gemini API.
        """
        # Format ML scores
        if ml_scores:
            ml_context = f"""--- ML MODEL SIGNALS ---
Recommendation Score: {ml_scores.get('recommendation_score', 0.0):.2f}
Risk Score (lower is better): {ml_scores.get('risk_score', 0.0):.2f}
Confidence: {ml_scores.get('confidence', 0.0):.2f}
Model Available: {ml_scores.get('model_available', False)}
"""
        else:
            ml_context = """--- ML MODEL SIGNALS ---
Model not available yet (loading...)
"""
        
        prompt = f"""{self.system_role}

--- EMPLOYEE CONTEXT ---
Department: {user_context.get('department', 'Unknown')}
Motivation Level: {user_context.get('motivation', 5)}/7
Self-Efficacy: {user_context.get('self_efficacy', 5)}/7
AI Usage Frequency: {self._resolve_ai_usage_frequency(user_context)}/5
Years in Company: {user_context.get('years_in_company', 'Unknown')}
Seniority: {self._resolve_seniority(user_context)}
Education Level: {user_context.get('education_level', 'Bachelor')}

--- RETRIEVED EMPLOYEE FACTS ---
{self._build_retrieved_facts_block(user_context)}

{ml_context}
--- INITIAL INSTRUCTION ---
This is the beginning of a training consultation.
Based on the employee profile, provide an initial assessment and recommendations.

--- MANDATORY JSON RESPONSE FORMAT ---
You MUST respond ONLY with this exact JSON structure (no other text):

{{
  "message": "Personalized greeting and initial assessment for the employee",
  "recommendations": {{
    "course": "Recommended course name or null",
    "mentor": "Suggested mentor profile or null",
    "plan_30_days": [
      "Week 1: action",
      "Week 2: action",
      "Week 3: action",
      "Week 4: action"
    ]
  }},
  "insights": {{
    "general": "General insight from training data",
    "department": "Department-specific pattern",
    "personal": "Employee profile-based insight"
  }},
  "metadata": {{
    "goal_detected": false,
    "goal_clarity": "low",
    "recommended_skill": null
  }},
  "risk_alert": null
}}

CRITICAL RULES:
- Respond ONLY with JSON. No text before or after.
- Use null for missing information, never empty strings.
- The JSON must be valid and parseable.
- Do not add explanations or markdown.
- If the employee asks about their own profile values, use the RETRIEVED EMPLOYEE FACTS above."""

        logger.debug("Initial prompt built successfully")
        return prompt

    def build_contextual_prompt(
        self,
        user_message: str,
        user_context: Dict[str, Any],
        rag_context: Optional[Dict[str, Any]],
        history: List[Dict[str, str]],
        ml_scores: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build contextual prompt for subsequent conversation turns.

        This method injects RAG context (from SQL, processed by Comp2) and
        conversation history to provide rich context to Gemini.

        Args:
            user_message: The current message from the employee
            user_context: Employee profile (same as build_initial_prompt)
            rag_context: SQL-enriched context from Comp2:
                - similar_profiles_summary (str)
                - department_insights (str)
                - top_courses (List[Dict])
                - avg_improvement (float)
                - risk_flags (List[str])
            history: Conversation history [{"role": "user"|"assistant", "content": "..."}]

        Returns:
            Formatted prompt string ready for Gemini API with full context.
        """

        # Default RAG context if none provided (first turn follow-up)
        if rag_context is None:
            rag_context = {
                "similar_profiles_summary": "No similar profiles analyzed yet",
                "department_insights": "Department data being loaded",
                "top_courses": [],
                "avg_improvement": 0,
                "risk_flags": [],
            }

        # Format top courses for readability
        courses_text = (
            ", ".join([c.get("title", "Unknown") for c in rag_context.get("top_courses", [])])
            if rag_context.get("top_courses")
            else "No courses available yet"
        )

        # Build conversation context (last turns)
        conversation_block = ""
        if history:
            conversation_block = "\n--- CONVERSATION HISTORY ---\n"
            for turn in history[-5:]:  # Show last 5 turns for context
                role = turn.get("role", "unknown").upper()
                content = turn.get("content", "")
                conversation_block += f"{role}: {content}\n"

        # Format ML scores
        if ml_scores:
            ml_context = f"""--- ML MODEL SIGNALS ---
Recommendation Score: {ml_scores.get('recommendation_score', 0.0):.2f}
Risk Score (lower is better): {ml_scores.get('risk_score', 0.0):.2f}
Confidence: {ml_scores.get('confidence', 0.0):.2f}
Model Available: {ml_scores.get('model_available', False)}
"""
        else:
            ml_context = """--- ML MODEL SIGNALS ---
Model not available yet
"""
        
        # Format mentores and programas
        mentores = rag_context.get("recommended_mentors", []) if rag_context else []
        programas = rag_context.get("relevant_programs", []) if rag_context else []
        hybrid_context = rag_context.get("hybrid_context", {}) if rag_context else {}
        
        mentores_text = ", ".join([m.get("nombre", "Unknown") for m in mentores]) if mentores else "None available"
        mentor_contacts_text = (
            "; ".join(
                [
                    f"{m.get('nombre', 'Unknown')} ({m.get('email')})"
                    for m in mentores
                    if m.get("email")
                ]
            )
            if mentores
            else "None"
        )
        programas_text = ", ".join([p.get("title", "Unknown") for p in programas]) if programas else "None available"
        citations = hybrid_context.get("citations", []) if isinstance(hybrid_context, dict) else []
        citations_text = (
            ", ".join(
                [
                    f"{c.get('title', 'Unknown')} ({c.get('source', 'unknown')})"
                    for c in citations[:8]
                ]
            )
            if citations
            else "None"
        )
        retrieval_eval = hybrid_context.get("evaluation", {}) if isinstance(hybrid_context, dict) else {}
        retrieval_eval_text = (
            "; ".join([f"{k}: {v}" for k, v in retrieval_eval.items()])
            if retrieval_eval
            else "N/A"
        )
        
        prompt = f"""{self.system_role}
        
--- EMPLOYEE CONTEXT ---
Department: {user_context.get('department', 'Unknown')}
Motivation Level: {user_context.get('motivation', 5)}/7
Self-Efficacy: {user_context.get('self_efficacy', 5)}/7
AI Usage Frequency: {self._resolve_ai_usage_frequency(user_context)}/5
Years in Company: {user_context.get('years_in_company', 'Unknown')}
Seniority: {self._resolve_seniority(user_context)}
Education Level: {user_context.get('education_level', 'Bachelor')}

--- RETRIEVED EMPLOYEE FACTS ---
{self._build_retrieved_facts_block(user_context)}

{ml_context}
--- RAG ENRICHED CONTEXT (from SQL data) ---
Similar Profiles Summary: {rag_context.get('similar_profiles_summary', 'N/A')}
Department Insights: {rag_context.get('department_insights', 'N/A')}
Average Improvement: {rag_context.get('avg_improvement', 0)}%
Top Recommended Courses: {courses_text}
Risk Flags: {', '.join(rag_context.get('risk_flags', [])) if rag_context.get('risk_flags') else 'None'}

--- MENTORS & PROGRAMS ---
Available Mentors: {mentores_text}
Mentor Contacts: {mentor_contacts_text}
Relevant Programs: {programas_text}

--- HYBRID RAG TRACE ---
Top citations: {citations_text}
Retrieval quality snapshot: {retrieval_eval_text}

{conversation_block}

--- CURRENT EMPLOYEE MESSAGE ---
"{user_message}"

--- MANDATORY JSON RESPONSE FORMAT ---
You MUST respond ONLY with this exact JSON structure (no other text):

{{
  "message": "Clear and personalized response addressing the employee's message",
  "recommendations": {{
    "course": "Recommended course based on context or null",
    "mentor": "Suggested mentor role or null",
    "plan_30_days": [
      "Week 1: specific action",
      "Week 2: specific action",
      "Week 3: specific action",
      "Week 4: specific action"
    ]
  }},
  "insights": {{
    "general": "Insight based on aggregated training data patterns",
    "department": "Department-specific pattern or trend",
    "personal": "Insight tailored to this employee's profile and message"
  }},
  "metadata": {{
    "goal_detected": true_or_false,
    "goal_clarity": "high_or_medium_or_low",
    "recommended_skill": "Detected skill or null"
  }},
  "risk_alert": null_or_"risk_type"
}}

CRITICAL RULES FOR RESPONSE:
- Respond ONLY with JSON. Absolutely no text before, after, or mixed with JSON.
- Use null for missing information (not empty strings, not "N/A").
- The JSON must be valid and properly formatted.
- The 'message' field should be conversational and helpful.
- The 'plan_30_days' array should contain 4 concrete, actionable steps.
- Do not use markdown, code blocks, or any formatting outside JSON.
- If the employee message contains a clear learning goal, set goal_detected to true.
- If a skill is mentioned or inferred, include it in recommended_skill.
- If the employee asks how to contact a mentor, use the Mentor Contacts emails from context.
- If the employee asks about their own profile values, use the RETRIEVED EMPLOYEE FACTS above."""

        logger.debug(
            f"Contextual prompt built (history: {len(history)} turns, "
            f"rag_context: {bool(rag_context)})"
        )
        return prompt

    def validate_prompt_includes_json_instruction(self, prompt: str) -> bool:
        """
        Validate that prompt includes mandatory JSON format instruction.
        
        Args:
            prompt: The built prompt string
            
        Returns:
            True if prompt contains JSON format block, False otherwise
        """
        return "MANDATORY JSON RESPONSE FORMAT" in prompt and "{" in prompt and "}" in prompt
