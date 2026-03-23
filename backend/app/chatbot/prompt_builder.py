"""
PromptBuilder for EvaluAI Chatbot Core.

Constructs structured prompts to ensure Gemini 2.5 Flash responds in JSON format.
The goal is to force deterministic, parseable JSON output from the LLM.
"""

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
Predictive Motivation: {ml_scores.get('predicted_motivation', 0.0):.2f}/7
Risk Score (lower is better): {ml_scores.get('risk_score', 0.0):.2f}
Confidence: {ml_scores.get('confidence', 0.0):.2f}
Dependency Profile: {ml_scores.get('dependency_prediction', 'unknown').upper()}
Model Available: {ml_scores.get('model_available', False)}
"""
        else:
            ml_context = """--- ML MODEL SIGNALS ---
Model not available yet (loading...)
"""
        
        prompt = f"""{self.system_role}

--- EMPLOYEE CONTEXT ---
Role: {user_context.get('role', 'Empleado')}
Department: {user_context.get('department', 'Unknown')}
Years in Company: {user_context.get('years_in_company', 0)}
Motivation Level: {user_context.get('motivation', 5)}/7
Self-Efficacy: {user_context.get('self_efficacy', 5)}/7
AI Usage Frequency: {user_context.get('ai_usage', 3)}/5
Primary AI Tool: {user_context.get('primary_tool', 'Unknown')}
Education Level: {user_context.get('education_level', 'Bachelor')}

{ml_context}
--- INITIAL INSTRUCTION ---
This is the beginning of a training consultation.
Based on the employee profile, provide an initial assessment and recommendations.

--- MANDATORY JSON RESPONSE FORMAT ---
You MUST respond ONLY with this exact JSON structure (no other text):

{{
  "message": "Personalized greeting and initial assessment for the employee",
  "recommendations": {{
    "course": "Proactively select one of the Top Recommended Courses from the context",
    "mentor": "Select ONE exact name from the Available Mentors list.", 
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
- Do not add explanations or markdown."""

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
        mentores_text = ", ".join([m.get("nombre", "Unknown") for m in mentores]) if mentores else "None available"
        programas_text = ", ".join([p.get("title", "Unknown") for p in programas]) if programas else "None available"        
        prompt = f"""{self.system_role}
        
--- EMPLOYEE CONTEXT ---
Department: {user_context.get('department', 'Unknown')}
Years in Company: {user_context.get('years_in_company', 0)}
Motivation Level: {user_context.get('motivation', 5)}/7
Self-Efficacy: {user_context.get('self_efficacy', 5)}/7
AI Usage Frequency: {user_context.get('ai_usage', 3)}/5
Primary AI Tool: {user_context.get('primary_tool', 'Unknown')}
Education Level: {user_context.get('education_level', 'Bachelor')}

{ml_context}
--- RAG ENRICHED CONTEXT (from SQL data) ---
Similar Profiles Summary: {rag_context.get('similar_profiles_summary', 'N/A')}
Department Insights: {rag_context.get('department_insights', 'N/A')}
Average Improvement: {rag_context.get('avg_improvement', 0)}%
Top Recommended Courses: {courses_text}
Risk Flags: {', '.join(rag_context.get('risk_flags', [])) if rag_context.get('risk_flags') else 'None'}

--- MENTORS & PROGRAMS ---
Available Mentors: {mentores_text}
Relevant Programs: {programas_text}

{conversation_block}

--- CURRENT EMPLOYEE MESSAGE ---
"{user_message}"

--- MANDATORY JSON RESPONSE FORMAT ---
You MUST respond ONLY with this exact JSON structure (no other text):

{{
  "message": "Start by greeting the employee. Then, briefly mention your ML insights translating probabilities to natural percentages (e.g. if the Risk score is 0.66 say '66%'). Specifically mention the Predictive Motivation (out of 7) and the Recommendation Score (out of 10), and contextualize them empathetically to their query.",
  "recommendations": {{
    "course": "Proactively select one of the Top Recommended Courses from the context",
    "mentor": "Proactively select one relevant name from the Available Mentors list. Do not leave null.",
    "plan_30_days": [
      "Semana 1: acción específica",
      "Semana 2: acción específica",
      "Semana 3: acción específica",
      "Semana 4: acción específica"
    ]
  }},
  "insights": {{
    "general": "Provide a metric insight using exactly this format based on context: 'Empleados con perfil similar mejoraron un XX% su autoeficacia tras cursos similares'",
    "department": "Insight linking their department data to the Recommended Course",
    "personal": "Feedback explicitly addressing their Risk Score or Confidence level from the ML MODEL SIGNALS"
  }},
  "metadata": {{
    "goal_detected": true,
    "goal_clarity": "high",
    "recommended_skill": "Detected skill or focus area"
  }},
  "risk_alert": null_or_"risk_type"
}}

CRITICAL RULES FOR RESPONSE:
- Respond ONLY with JSON. Absolutely no text before, after, or mixed with JSON.
- BE PROACTIVE: ALWAYS recommend a course, a mentor, and a 30-day plan, even if the user just says 'hola'. You MUST select EXACTLY ONE mentor from the 'Available Mentors' list. If Mentors is 'None available' NEVER invent fake names. Use the context provided to cater them to their profile.
- SHOWCASE METRICS: You must explicitly mention their ML stats, autoeficacia, and improvement % in your answers to demonstrate that the AI knows their profile depth.
- ML BEHAVIOR: Adapt your tone based on Risk Score and Years in Company. If Dependency Profile is HIGH, advise caution with AI copy-pasting. If they feel unmotivated, act highly supportive.
- ADAPTABILITY FIRST: If the user changes their mind or explicitly asks for a different topic (e.g. Soft Skills instead of Data), you MUST respect their current request immediately. Pivot your course and mentor recommendations to match their NEW interest, ignoring their previous history if it conflicts.
- CONSISTENCY: Ensure your conversational message matches your JSON output. If you select a mentor in the "mentor" JSON field, you must act as if they are actively assigned to the user in your text message. Do not say you are "still looking" if you are outputting a name.
- Use null ONLY if data is truly completely missing from context.
- The JSON must be valid and properly formatted.
"""
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