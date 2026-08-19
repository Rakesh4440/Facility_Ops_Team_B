from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from components.theme import apply_theme
from utils.auth import require_auth
from utils.maintenance import load_schedules
from utils.maintenance_history import load_maintenance_history
from utils.work_orders import load_work_orders


try:
    st.set_page_config(
        page_title="Maintenance status dashboard",
        page_icon=":material/monitoring:",
        layout="wide",
    )
except Exception:
    pass
apply_theme()



schedules = load_schedules()
work_orders = load_work_orders()
maintenance_history = load_maintenance_history()
today = date.today()
due_dates = pd.to_datetime(schedules["Next Due Date"], errors="coerce").dt.date
active = schedules["Active"].eq("Yes")
overdue = active & due_dates.lt(today)
upcoming = active & due_dates.ge(today) & due_dates.le(today + pd.Timedelta(days=7))
open_orders = work_orders["Status"].isin(["Open", "In Progress"])
preventive_mask = work_orders["Issue"].astype(str).str.startswith("Preventive maintenance")
open_preventive = open_orders & preventive_mask
open_reactive = open_orders & ~preventive_mask
completed_count = int(work_orders["Status"].eq("Completed").sum())

st.markdown(
    '<div class="hero-eyebrow">Operations control</div>',
    unsafe_allow_html=True,
)
st.title(":material/monitoring: Maintenance status dashboard")
st.caption(
    "One live view of preventive schedules, open work, technician load, and completed history."
)

health_bits = []
if int(overdue.sum()) == 0:
    health_bits.append(":green-badge[:material/check_circle: No overdue]")
else:
    health_bits.append(f":red-badge[:material/warning: {int(overdue.sum())} overdue]")
if int(upcoming.sum()):
    health_bits.append(f":orange-badge[:material/event_upcoming: {int(upcoming.sum())} due soon]")
else:
    health_bits.append(":blue-badge[:material/event_available: Clear week]")
health_bits.append(f":violet-badge[:material/build: {int(open_orders.sum())} open WOs]")
st.markdown(" ".join(health_bits))

with st.container(horizontal=True):
    st.metric(
        ":material/event_note: Active schedules",
        int(active.sum()),
        border=True,
    )
    st.metric(
        ":material/event_upcoming: Due in 7 days",
        int(upcoming.sum()),
        delta=f"{int(upcoming.sum())} upcoming" if int(upcoming.sum()) else "None upcoming",
        delta_color="off",
        border=True,
    )
    st.metric(
        ":material/event_busy: Overdue",
        int(overdue.sum()),
        delta=f"-{int(overdue.sum())} need action" if int(overdue.sum()) else "All clear",
        delta_color="inverse" if int(overdue.sum()) else "normal",
        border=True,
    )
    st.metric(
        ":material/handyman: Open preventive",
        int(open_preventive.sum()),
        border=True,
    )
    st.metric(
        ":material/report: Open reactive",
        int(open_reactive.sum()),
        border=True,
    )
    st.metric(
        ":material/task_alt: Completed",
        completed_count if completed_count else len(maintenance_history),
        border=True,
    )

status_chart_col, workload_chart_col, mix_chart_col = st.columns([1.15, 1.15, 1])
with status_chart_col:
    with st.container(border=True):
        st.subheader(":material/assignment: Work-order status")
        st.caption("How many jobs are open, in progress, or done.")
        status_summary = (
            work_orders["Status"]
            .value_counts()
            .reindex(["Open", "In Progress", "Completed"], fill_value=0)
            .rename_axis("Status")
            .reset_index(name="Work orders")
        )
        status_fig = px.bar(
            status_summary,
            x="Status",
            y="Work orders",
            color="Status",
            color_discrete_map={
                "Open": "#7c8cff",
                "In Progress": "#ffd166",
                "Completed": "#4de1d1",
            },
        )
        status_fig.update_layout(showlegend=False, height=280, yaxis_title=None, xaxis_title=None)
        st.plotly_chart(status_fig, width="stretch", config={"displayModeBar": False})

with workload_chart_col:
    with st.container(border=True):
        st.subheader(":material/engineering: Technician workload")
        st.caption("Active preventive schedules assigned to each person.")
        workload_summary = (
            schedules.loc[active, "Assigned To"]
            .value_counts()
            .rename_axis("Technician")
            .reset_index(name="Active schedules")
        )
        if workload_summary.empty:
            st.info("No active schedules are currently assigned.", icon=":material/info:")
        else:
            workload_fig = px.bar(
                workload_summary.sort_values("Active schedules"),
                x="Active schedules",
                y="Technician",
                orientation="h",
                color="Active schedules",
                color_continuous_scale=["#182747", "#7c8cff", "#4de1d1"],
            )
            workload_fig.update_layout(
                showlegend=False,
                height=280,
                coloraxis_showscale=False,
                xaxis_title=None,
                yaxis_title=None,
            )
            st.plotly_chart(workload_fig, width="stretch", config={"displayModeBar": False})

with mix_chart_col:
    with st.container(border=True):
        st.subheader(":material/category: Work mix")
        st.caption("Preventive vs reactive open jobs.")
        mix = pd.DataFrame(
            {
                "Type": ["Preventive", "Reactive"],
                "Open jobs": [int(open_preventive.sum()), int(open_reactive.sum())],
            }
        )
        if mix["Open jobs"].sum() == 0:
            st.success("No open work orders right now.", icon=":material/task_alt:")
        else:
            mix_fig = px.pie(
                mix,
                names="Type",
                values="Open jobs",
                color="Type",
                color_discrete_map={"Preventive": "#4de1d1", "Reactive": "#ff9b8e"},
                hole=0.55,
            )
            mix_fig.update_layout(height=280, margin={"t": 20, "b": 20, "l": 10, "r": 10})
            mix_fig.update_traces(textposition="inside", textinfo="label+value")
            st.plotly_chart(mix_fig, width="stretch", config={"displayModeBar": False})

attention_tab, open_tab, history_tab = st.tabs(
    [
        ":material/priority_high: Needs attention",
        ":material/build: Open work orders",
        ":material/history: History",
    ]
)

with attention_tab:
    with st.container(border=True):
        st.subheader("Schedules needing attention")
        st.caption("Overdue tasks and anything due in the next 7 days.")
        attention = schedules.loc[
            overdue | upcoming,
            ["Schedule ID", "Product ID", "Maintenance Task", "Assigned To", "Next Due Date"],
        ].copy()
        if attention.empty:
            st.success("No overdue or near-term maintenance tasks.", icon=":material/task_alt:")
        else:
            attention["Due date"] = pd.to_datetime(attention.pop("Next Due Date"))
            attention["Urgency"] = attention["Due date"].dt.date.map(
                lambda due_date: "Overdue" if due_date < today else "Due soon"
            )
            attention["Days"] = attention["Due date"].dt.date.map(
                lambda due_date: (today - due_date).days if due_date < today else (due_date - today).days
            )
            attention = attention.sort_values("Due date")
            st.dataframe(
                attention,
                hide_index=True,
                height=320,
                width="stretch",
                column_config={
                    "Schedule ID": st.column_config.TextColumn("Schedule", pinned=True),
                    "Product ID": st.column_config.TextColumn("Asset"),
                    "Maintenance Task": st.column_config.TextColumn("Task", width="large"),
                    "Assigned To": st.column_config.TextColumn("Technician"),
                    "Due date": st.column_config.DateColumn("Due date", format="DD MMM YYYY"),
                    "Urgency": st.column_config.TextColumn("Urgency"),
                    "Days": st.column_config.NumberColumn("Days", format="%d", help="Days overdue or days until due"),
                },
            )

with open_tab:
    with st.container(border=True):
        st.subheader("Open and in-progress work orders")
        st.caption("Includes both reactive repairs and generated preventive jobs.")
        open_view = work_orders.loc[open_orders].copy()
        if open_view.empty:
            st.success("Nothing open — all caught up.", icon=":material/task_alt:")
        else:
            open_view["Kind"] = open_view["Issue"].astype(str).map(
                lambda issue: "Preventive" if issue.startswith("Preventive maintenance") else "Reactive"
            )
            open_view["Due Date"] = pd.to_datetime(open_view["Due Date"], errors="coerce")
            open_view = open_view.sort_values("Due Date")
            st.dataframe(
                open_view[
                    ["ID", "Product ID", "Kind", "Issue", "Priority", "Assigned To", "Due Date", "Status"]
                ],
                hide_index=True,
                height=320,
                width="stretch",
                column_config={
                    "ID": st.column_config.TextColumn("Work order", pinned=True),
                    "Product ID": st.column_config.TextColumn("Asset"),
                    "Kind": st.column_config.TextColumn("Kind"),
                    "Issue": st.column_config.TextColumn("Issue", width="large"),
                    "Priority": st.column_config.TextColumn("Priority"),
                    "Assigned To": st.column_config.TextColumn("Technician"),
                    "Due Date": st.column_config.DateColumn("Due date", format="DD MMM YYYY"),
                    "Status": st.column_config.TextColumn("Status"),
                },
            )

with history_tab:
    with st.container(border=True):
        st.subheader("Recent maintenance history")
        st.caption("Completed work orders recorded for traceability.")
        if maintenance_history.empty:
            st.info(
                "Mark a work order as Completed on the Work orders page to build this history.",
                icon=":material/history:",
            )
        else:
            st.dataframe(
                maintenance_history.head(12),
                hide_index=True,
                height=320,
                width="stretch",
                column_config={
                    "Work order": st.column_config.TextColumn("Work order", pinned=True),
                    "Completed on": st.column_config.DateColumn("Completed on", format="DD MMM YYYY"),
                },
            )
