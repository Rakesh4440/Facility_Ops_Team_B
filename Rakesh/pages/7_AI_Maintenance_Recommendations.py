import streamlit as st

from components.theme import apply_theme
from utils.auth import require_auth
from utils.ai_assistant import (

    OllamaModelNotFoundError,
    OllamaServerUnavailableError,
    check_ollama_status,
    generate_maintenance_briefing,
)
from utils.maintenance import load_schedules
from utils.maintenance_recommendations import build_maintenance_recommendations
from utils.work_orders import load_work_orders


try:
    st.set_page_config(
        page_title="AI maintenance recommendations",
        page_icon=":material/auto_awesome:",
        layout="wide",
    )
except Exception:
    pass
apply_theme()



st.title(":material/auto_awesome: AI maintenance recommendations")
st.caption(
    "Prioritized actions are generated from your live schedules and work orders, "
    "with an optional local AI operations briefing."
)

recommendations = build_maintenance_recommendations(load_schedules(), load_work_orders())
priority_counts = recommendations["Priority"].value_counts()

with st.container(horizontal=True):
    st.metric(":material/crisis_alert: Critical actions", int(priority_counts.get("Critical", 0)), border=True)
    st.metric(":material/priority_high: High-priority actions", int(priority_counts.get("High", 0)), border=True)
    st.metric(":material/event: Planned actions", int(priority_counts.get("Medium", 0)), border=True)

with st.container(border=True):
    st.subheader(":material/recommend: Recommended actions")
    st.caption("Recommendations are ranked by operational urgency and explain the reason for each action.")
    st.dataframe(
        recommendations,
        hide_index=True,
        width="stretch",
        column_config={
            "Priority": st.column_config.TextColumn("Priority", pinned=True),
            "Recommendation": st.column_config.TextColumn("Recommended action", width="large"),
            "Why now": st.column_config.TextColumn("Why now", width="large"),
            "Due date": st.column_config.TextColumn("Due date"),
        },
    )

ollama_ready, ollama_status = check_ollama_status()

with st.container(border=True):
    st.subheader(":material/psychology: Local AI operations briefing")
    st.caption(
        "This button asks your local Ollama model to rewrite the recommendation table above into a short "
        "supervisor briefing. It does not invent new jobs — it only summarizes what is already listed."
    )
    if ollama_ready:
        st.success(ollama_status, icon=":material/check_circle:")
    else:
        st.warning(ollama_status, icon=":material/warning:")

    if st.button(
        "Generate AI briefing",
        icon=":material/auto_awesome:",
        type="primary",
        disabled=not ollama_ready,
    ):
        with st.spinner("Writing the operations briefing with the local model…"):
            try:
                st.session_state["maintenance_ai_briefing"] = generate_maintenance_briefing(
                    recommendations.to_dict(orient="records")
                )
                st.session_state["maintenance_ai_briefing_error"] = None
            except OllamaServerUnavailableError:
                st.session_state["maintenance_ai_briefing_error"] = (
                    "Ollama server is not running. The recommendations above remain available."
                )
            except OllamaModelNotFoundError:
                st.session_state["maintenance_ai_briefing_error"] = (
                    "llama3.2 model not found. Run `ollama pull llama3.2`, then try again."
                )
            except Exception as exc:
                st.session_state["maintenance_ai_briefing_error"] = (
                    f"Could not generate the AI briefing: {exc}"
                )

    error = st.session_state.get("maintenance_ai_briefing_error")
    if error:
        st.error(error, icon=":material/error:")

    briefing = st.session_state.get("maintenance_ai_briefing")
    if briefing:
        st.markdown("##### Shift briefing")
        st.info(briefing, icon=":material/campaign:")
