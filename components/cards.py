import streamlit as st

def kpi_cards(total, failure, air_temp, torque):

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "🏭 Total Machines",
            f"{total:,}"
        )

    with c2:
        st.metric(
            "🚨 Total Failures",
            f"{failure:,}"
        )

    with c3:
        st.metric(
            "🌡 Avg Air Temp",
            f"{air_temp:.2f} K"
        )

    with c4:
        st.metric(
            "⚙ Avg Torque",
            f"{torque:.2f} Nm"
        )