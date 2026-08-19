import streamlit as st
from components.theme import apply_theme
from utils.auth import is_authenticated, get_current_user, render_user_sidebar

st.set_page_config(
    page_title="FacilityOps AI Platform",
    page_icon="🏭",
    layout="wide"
)

apply_theme()

if not is_authenticated():
    # HIDE SIDEBAR COMPLETELY WHEN NOT LOGGED IN
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
        }
        .block-container {
            max-width: 900px !important;
            padding-top: 2rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    from components.auth_ui import render_auth_page
    render_auth_page()
else:
    user = get_current_user()
    role = user.get("role", "technician").lower()

    render_user_sidebar()

    if role == "admin":
        nav_pages = {
            "Operations & Dashboards": [
                st.Page("pages/1_Maintenance_Status_Dashboard.py", title="Maintenance Status Dashboard", icon="📊", default=True),
                st.Page("pages/3_Dashboard.py", title="Facility Dashboard", icon="📉"),
            ],
            "Diagnostics & Execution": [
                st.Page("pages/4_Machine_Explorer.py", title="Machine Explorer", icon="🔍"),
                st.Page("pages/5_Work_Orders.py", title="Work Orders", icon="📋"),
                st.Page("pages/6_Maintenance_Schedules.py", title="Maintenance Schedules", icon="📅"),
            ],
            "Intelligence & Analytics": [
                st.Page("pages/2_EDA.py", title="EDA Analytics", icon="📈"),
                st.Page("pages/7_AI_Maintenance_Recommendations.py", title="AI Recommendations", icon="🤖"),
            ]
        }
    else:
        # TECHNICIAN ROLE: STRICTLY ONLY THE 4 OPERATIONAL PAGES!
        nav_pages = {
            "Technician Workspace": [
                st.Page("pages/1_Maintenance_Status_Dashboard.py", title="Maintenance Status Dashboard", icon="📊", default=True),
                st.Page("pages/4_Machine_Explorer.py", title="Machine Explorer", icon="🔍"),
                st.Page("pages/5_Work_Orders.py", title="Work Orders", icon="📋"),
                st.Page("pages/6_Maintenance_Schedules.py", title="Maintenance Schedules", icon="📅"),
            ]
        }

    pg = st.navigation(nav_pages)
    pg.run()
