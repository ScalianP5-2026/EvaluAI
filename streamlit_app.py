from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="EvaluAI", page_icon="EA", layout="wide")

DEFAULT_API_BASE_URL = os.getenv("EVALUAI_API_BASE_URL", "http://localhost:8000/api/v1")


def _api_get(base_url: str, path: str) -> dict[str, Any]:
    response = requests.get(f"{base_url}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


def _api_post(base_url: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{base_url}{path}", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def _api_upload_csv(base_url: str, filename: str, content: bytes) -> dict[str, Any]:
    files = {"file": (filename, content, "text/csv")}
    response = requests.post(f"{base_url}/surveys/upload", files=files, timeout=60)
    response.raise_for_status()
    return response.json()


st.title("EvaluAI - Training Impact with AI")
st.caption("Dashboard + Chatbot + NLP analyzer")

st.sidebar.subheader("Settings")
api_base_url = st.sidebar.text_input("API base URL", value=DEFAULT_API_BASE_URL)
uploaded_file = st.sidebar.file_uploader("Upload survey CSV", type=["csv"])

if st.sidebar.button("Send CSV to API"):
    if uploaded_file is None:
        st.sidebar.error("Select a CSV file first.")
    else:
        try:
            upload_payload = _api_upload_csv(
                api_base_url,
                uploaded_file.name,
                uploaded_file.getvalue(),
            )
            st.sidebar.success(upload_payload.get("message", "Dataset updated"))
        except Exception as exc:
            st.sidebar.error(f"CSV upload failed: {exc}")


tab_dashboard, tab_chatbot, tab_nlp = st.tabs(
    [
        "1) Dashboard de analisis",
        "2) Chatbot inteligente",
        "3) NLP opinion analyzer",
    ]
)


with tab_dashboard:
    if st.button("Refresh dashboard"):
        st.session_state.pop("dashboard", None)

    if "dashboard" not in st.session_state:
        try:
            st.session_state.dashboard = _api_get(api_base_url, "/dashboard/summary")
        except Exception as exc:
            st.error(f"Cannot load dashboard: {exc}")
            st.stop()

    dashboard = st.session_state.dashboard
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Employees", dashboard["total_employees"])
    col2.metric("Avg motivation", dashboard["avg_motivation"])
    col3.metric("Avg self efficacy", dashboard["avg_self_efficacy"])
    col4.metric("Avg AI use score", dashboard["avg_ai_use_score"])

    st.markdown("### AI usage distribution")
    usage_df = pd.DataFrame(dashboard["usage_distribution"])
    if not usage_df.empty:
        st.bar_chart(usage_df.set_index("level"))

    st.markdown("### Correlations")
    corr_df = pd.DataFrame(dashboard["correlations"])
    st.dataframe(corr_df, use_container_width=True)

    st.markdown("### Auto insights")
    for insight in dashboard["insights"]:
        st.write(f"- {insight}")


with tab_chatbot:
    st.write("A lightweight recommendation assistant for personalized learning plans.")

    with st.form("chat_form"):
        role = st.selectbox(
            "Employee role",
            [
                "Data Analyst",
                "Technology",
                "HR",
                "Finance",
                "Operations",
                "Marketing",
                "Sales",
            ],
        )
        goal = st.text_input("Learning goal", value="Python avanzado para ML")
        ai_usage = st.selectbox(
            "Current AI usage",
            ["never", "rarely", "sometimes", "frequently", "always"],
            index=2,
        )
        self_efficacy = st.slider(
            "Self efficacy",
            min_value=1.0,
            max_value=10.0,
            value=6.5,
        )
        motivation = st.slider(
            "Motivation",
            min_value=1.0,
            max_value=10.0,
            value=7.0,
        )
        submitted = st.form_submit_button("Ask assistant")

    if submitted:
        payload = {
            "employee_role": role,
            "learning_goal": goal,
            "ai_usage": ai_usage,
            "self_efficacy": self_efficacy,
            "motivation": motivation,
        }
        try:
            chat_response = _api_post(api_base_url, "/chat/query", payload)
            st.info(chat_response["message"])

            st.markdown("### Recommended courses")
            for item in chat_response["recommended_courses"]:
                st.write(f"- {item}")

            st.markdown("### Recommended mentor")
            st.write(chat_response.get("recommended_mentor", "No mentor found"))

            st.markdown("### 30-day plan")
            for step in chat_response["thirty_day_plan"]:
                st.write(f"- {step}")

            st.write(
                "Estimated improvement for similar profiles: "
                f"{chat_response['similar_profile_improvement']}%"
            )
        except Exception as exc:
            st.error(f"Chatbot request failed: {exc}")


with tab_nlp:
    raw_comments = st.text_area(
        "Paste one comment per line",
        value=(
            "Good support from mentor\n"
            "Training was hard and confusing\n"
            "Useful prompts saved time"
        ),
        height=150,
    )

    if st.button("Analyze comments"):
        comments = [line.strip() for line in raw_comments.splitlines() if line.strip()]
        try:
            nlp_response = _api_post(api_base_url, "/nlp/analyze", {"comments": comments})
            col_a, col_b = st.columns(2)
            col_a.metric("Overall sentiment", nlp_response["overall_sentiment"])
            col_b.metric("Sentiment score", nlp_response["sentiment_score"])

            st.markdown("### Topics")
            topics_df = pd.DataFrame(nlp_response["topics"])
            if topics_df.empty:
                st.write("No topics detected")
            else:
                st.dataframe(topics_df, use_container_width=True)

            st.markdown("### Group recommendations")
            for recommendation in nlp_response["group_recommendations"]:
                st.write(f"- {recommendation}")
        except Exception as exc:
            st.error(f"NLP analysis failed: {exc}")
