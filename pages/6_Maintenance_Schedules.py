import calendar
from datetime import date

import pandas as pd
import streamlit as st

from components.theme import apply_theme
from utils.auth import require_auth
from utils.maintenance import load_schedules, next_schedule_id, save_schedules
from utils.maintenance_checklists import default_checklist, delete_checklist, load_checklist, save_checklist
from utils.work_orders import generate_preventive_work_order, load_work_orders, preventive_work_order_exists
from utils.auth import get_current_user

try:
    st.set_page_config(page_title="Maintenance schedules", page_icon=":material/calendar_month:", layout="wide")
except Exception:
    pass
apply_theme()



if "maintenance_schedules" not in st.session_state:
    st.session_state["maintenance_schedules"] = load_schedules()
st.session_state.setdefault("schedule_notice", None)

st.title(":material/calendar_month: Preventive maintenance schedules")
st.caption("Set a maintenance frequency, assign the technician, and keep every planned task on schedule.")

notice = st.session_state.pop("schedule_notice", None)
if notice:
    st.success(notice, icon=":material/check_circle:")

schedules = st.session_state["maintenance_schedules"]
schedule_ids = schedules["Schedule ID"].tolist()
machine_types = ["M", "L", "H"]
frequencies = ["Daily", "Weekly", "Monthly", "Quarterly", "Semi-annual", "Annual"]


def schedule_label(schedule_id: str) -> str:
    row = schedules.loc[schedules["Schedule ID"].eq(schedule_id)].iloc[0]
    return f"{schedule_id} — {row['Product ID']}: {row['Maintenance Task']}"


due_dates = pd.to_datetime(schedules["Next Due Date"], errors="coerce").dt.date
today = date.today()
active = schedules["Active"].eq("Yes")
overdue = active & due_dates.lt(today)
upcoming = active & due_dates.ge(today) & due_dates.le(today + pd.Timedelta(days=7))

with st.container(horizontal=True):
    st.metric(":material/event_note: Active schedules", int(active.sum()), border=True)
    st.metric(":material/event_upcoming: Due in 7 days", int(upcoming.sum()), border=True)
    st.metric(":material/event_busy: Overdue", int(overdue.sum()), border=True)
    st.metric(":material/engineering: Assigned technicians", schedules.loc[active, "Assigned To"].nunique(), border=True)

with st.container(border=True):
    st.subheader(":material/calendar_month: Maintenance calendar")
    st.caption("Select a month to see planned preventive-maintenance tasks on their due dates.")
    calendar_month = st.date_input(
        "Calendar month",
        value=date(today.year, today.month, 1),
        key="maintenance_calendar_month",
    )
    selected_year, selected_month = calendar_month.year, calendar_month.month
    month_start = date(selected_year, selected_month, 1)
    month_end = date(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1])
    calendar_schedules = schedules.copy()
    calendar_schedules["Due date"] = pd.to_datetime(
        calendar_schedules["Next Due Date"], errors="coerce"
    ).dt.date
    calendar_schedules = calendar_schedules[
        calendar_schedules["Due date"].between(month_start, month_end)
        & calendar_schedules["Active"].eq("Yes")
    ]

    weekday_columns = st.columns(7)
    for column, weekday in zip(weekday_columns, calendar.day_abbr):
        column.caption(weekday)

    for week in calendar.monthcalendar(selected_year, selected_month):
        day_columns = st.columns(7)
        for column, day_number in zip(day_columns, week):
            with column:
                if not day_number:
                    st.write("")
                    continue
                day_date = date(selected_year, selected_month, day_number)
                entries = calendar_schedules[calendar_schedules["Due date"] == day_date]
                with st.container(border=True):
                    day_label = f"**{day_number}**"
                    if day_date == today:
                        day_label += "  :material/today:"
                    st.markdown(day_label)
                    if not entries.empty:
                        for _, entry in entries.head(2).iterrows():
                            st.caption(f":material/build: {entry['Product ID']} — {entry['Maintenance Task']}")
                        if len(entries) > 2:
                            st.caption(f"+{len(entries) - 2} more task(s)")
    if calendar_schedules.empty:
        st.info("No active maintenance tasks are scheduled for this month.", icon=":material/event_available:")

with st.container(border=True):
    st.subheader(":material/event_upcoming: Upcoming maintenance")
    st.caption("Active preventive-maintenance tasks due today or within the next seven days, ordered by urgency.")
    upcoming_schedules = schedules.loc[
        upcoming,
        ["Schedule ID", "Product ID", "Machine Type", "Maintenance Task", "Assigned To", "Next Due Date", "Frequency"],
    ].copy()
    if upcoming_schedules.empty:
        st.info("No active maintenance is due in the next seven days.", icon=":material/event_available:")
    else:
        upcoming_schedules["Due date"] = pd.to_datetime(upcoming_schedules["Next Due Date"])
        upcoming_schedules["Days until due"] = (upcoming_schedules["Due date"].dt.date - today).apply(lambda value: value.days)
        upcoming_schedules = upcoming_schedules.drop(columns="Next Due Date").sort_values(
            ["Days until due", "Due date", "Schedule ID"]
        )
        st.dataframe(
            upcoming_schedules,
            hide_index=True,
            width="stretch",
            column_config={
                "Schedule ID": st.column_config.TextColumn("Schedule", pinned=True),
                "Due date": st.column_config.DateColumn("Due date", format="DD MMM YYYY"),
                "Days until due": st.column_config.NumberColumn("Days until due", format="%d"),
            },
        )

with st.container(border=True):
    st.subheader(":material/event_busy: Overdue maintenance")
    st.caption("Active preventive-maintenance tasks that have passed their scheduled due date.")
    overdue_schedules = schedules.loc[
        overdue,
        ["Schedule ID", "Product ID", "Machine Type", "Maintenance Task", "Assigned To", "Next Due Date", "Frequency"],
    ].copy()
    if overdue_schedules.empty:
        st.success("No active maintenance tasks are overdue.", icon=":material/task_alt:")
    else:
        overdue_schedules["Due date"] = pd.to_datetime(overdue_schedules["Next Due Date"])
        overdue_schedules["Days overdue"] = (today - overdue_schedules["Due date"].dt.date).apply(
            lambda value: value.days
        )
        overdue_schedules = overdue_schedules.drop(columns="Next Due Date").sort_values(
            ["Days overdue", "Due date", "Schedule ID"], ascending=[False, True, True]
        )
        st.warning(
            f"{len(overdue_schedules)} active maintenance task(s) need immediate attention.",
            icon=":material/warning:",
        )
        st.dataframe(
            overdue_schedules,
            hide_index=True,
            width="stretch",
            column_config={
                "Schedule ID": st.column_config.TextColumn("Schedule", pinned=True),
                "Due date": st.column_config.DateColumn("Due date", format="DD MMM YYYY"),
                "Days overdue": st.column_config.NumberColumn("Days overdue", format="%d"),
            },
        )

create_col, schedule_col = st.columns((1, 1.45))
with create_col:
    with st.container(border=True):
        st.subheader(":material/add_task: Add a schedule")
        st.caption("Each saved schedule can later generate a work order when it becomes due.")
        with st.form("create_schedule", clear_on_submit=True):
            product_id = st.text_input("Product ID", placeholder="For example, M14860")
            machine_type = st.selectbox("Machine type", ["M", "L", "H"])
            task = st.text_input("Maintenance task", placeholder="For example, Inspect spindle vibration")
            frequency = st.selectbox("Maintenance frequency", ["Daily", "Weekly", "Monthly", "Quarterly", "Semi-annual", "Annual"])
            technician = st.text_input("Assign technician", placeholder="For example, A. Sharma")
            next_due_date = st.date_input("First due date", value=today)
            submitted = st.form_submit_button("Save maintenance schedule", icon=":material/save:", type="primary")

        if submitted:
            if not all([product_id.strip(), task.strip(), technician.strip()]):
                st.warning("Enter a Product ID, maintenance task, and assigned technician.", icon=":material/warning:")
            else:
                new_schedule = pd.DataFrame([{
                    "Schedule ID": next_schedule_id(schedules),
                    "Product ID": product_id.strip().upper(),
                    "Machine Type": machine_type,
                    "Maintenance Task": task.strip(),
                    "Frequency": frequency,
                    "Assigned To": technician.strip(),
                    "Next Due Date": next_due_date.isoformat(),
                    "Active": "Yes",
                }])
                st.session_state["maintenance_schedules"] = pd.concat([schedules, new_schedule], ignore_index=True)
                save_schedules(st.session_state["maintenance_schedules"])
                st.session_state["schedule_notice"] = "Preventive maintenance schedule saved."
                st.rerun()

with schedule_col:
    with st.container(border=True):
        st.subheader(":material/format_list_bulleted: Scheduled maintenance")
        st.caption("Schedules are ordered by their next due date.")
        status_filter = st.segmented_control("Show schedules", ["Active", "All", "Overdue"], default="Active")
        shown_schedules = schedules.copy()
        if status_filter == "Active":
            shown_schedules = shown_schedules[active]
        elif status_filter == "Overdue":
            shown_schedules = shown_schedules[overdue]
        st.dataframe(
            shown_schedules,
            hide_index=True,
            height=340,
            width="stretch",
            column_config={
                "Schedule ID": st.column_config.TextColumn("Schedule", pinned=True),
                "Next Due Date": st.column_config.DateColumn("Next due", format="DD MMM YYYY"),
                "Active": st.column_config.TextColumn("Active"),
            },
        )

user = get_current_user()
is_admin = user and user.get("role", "").lower() == "admin"

if schedule_ids:
    if is_admin:
        update_schedule_col, delete_schedule_col = st.columns(2)
    else:
        update_schedule_col = st.container()
    
    with update_schedule_col:
        with st.container(border=True):
            st.subheader(":material/edit_note: Update schedule")
            st.caption("Change task details, technician, due date, or mark a schedule inactive.")
            edit_schedule_id = st.selectbox(
                "Select schedule",
                schedule_ids,
                format_func=schedule_label,
                key="edit_schedule",
            )
            edit_row = schedules.loc[schedules["Schedule ID"].eq(edit_schedule_id)].iloc[0]
            with st.form("update_schedule_form"):
                edit_product_id = st.text_input("Product ID", value=edit_row["Product ID"])
                edit_machine_type = st.selectbox(
                    "Machine type",
                    machine_types,
                    index=machine_types.index(edit_row["Machine Type"]),
                )
                edit_task = st.text_input("Maintenance task", value=edit_row["Maintenance Task"])
                edit_frequency = st.selectbox(
                    "Maintenance frequency",
                    frequencies,
                    index=frequencies.index(edit_row["Frequency"]),
                )
                edit_technician = st.text_input("Assign technician", value=edit_row["Assigned To"])
                edit_due_date = st.date_input(
                    "Next due date",
                    value=pd.to_datetime(edit_row["Next Due Date"]).date(),
                    format="YYYY/MM/DD",
                )
                edit_active = st.selectbox(
                    "Active",
                    ["Yes", "No"],
                    index=0 if edit_row["Active"] == "Yes" else 1,
                    help="Set to No to hide a schedule from the calendar without deleting it.",
                )
                if st.form_submit_button("Save schedule changes", icon=":material/save:", type="primary"):
                    if not all([edit_product_id.strip(), edit_task.strip(), edit_technician.strip()]):
                        st.warning(
                            "Enter a Product ID, maintenance task, and assigned technician.",
                            icon=":material/warning:",
                        )
                    else:
                        row_index = schedules.index[schedules["Schedule ID"].eq(edit_schedule_id)][0]
                        st.session_state["maintenance_schedules"].loc[row_index, "Product ID"] = (
                            edit_product_id.strip().upper()
                        )
                        st.session_state["maintenance_schedules"].loc[row_index, "Machine Type"] = edit_machine_type
                        st.session_state["maintenance_schedules"].loc[row_index, "Maintenance Task"] = (
                            edit_task.strip()
                        )
                        st.session_state["maintenance_schedules"].loc[row_index, "Frequency"] = edit_frequency
                        st.session_state["maintenance_schedules"].loc[row_index, "Assigned To"] = (
                            edit_technician.strip()
                        )
                        st.session_state["maintenance_schedules"].loc[row_index, "Next Due Date"] = (
                            edit_due_date.isoformat()
                        )
                        st.session_state["maintenance_schedules"].loc[row_index, "Active"] = edit_active
                        save_schedules(st.session_state["maintenance_schedules"])
                        st.session_state["schedule_notice"] = f"{edit_schedule_id} updated."
                        st.rerun()

    if is_admin:
        with delete_schedule_col:
            with st.container(border=True):
                st.subheader(":material/delete_outline: Delete schedule")
                st.caption("Removal is saved permanently. Generated work orders are not deleted.")
                delete_schedule_id = st.selectbox(
                    "Select schedule",
                    schedule_ids,
                    format_func=schedule_label,
                    key="delete_schedule",
                )
                confirm_delete_schedule = st.checkbox("I confirm that this schedule should be deleted.")
                if st.button("Delete schedule", icon=":material/delete:"):
                    if not confirm_delete_schedule:
                        st.warning("Confirm deletion before removing the schedule.", icon=":material/warning:")
                    else:
                        delete_checklist(delete_schedule_id)
                        st.session_state["maintenance_schedules"] = (
                            st.session_state["maintenance_schedules"]
                            .loc[st.session_state["maintenance_schedules"]["Schedule ID"] != delete_schedule_id]
                            .reset_index(drop=True)
                        )
                        save_schedules(st.session_state["maintenance_schedules"])
                        st.session_state["schedule_notice"] = f"{delete_schedule_id} deleted."
                        st.rerun()

with st.container(border=True):
    st.subheader(":material/assignment_add: Generate preventive work order")
    st.caption("Create one open work order from a scheduled task. The schedule ID is retained in the work-order issue for traceability.")
    work_order_schedule_id = st.selectbox(
        "Select a schedule for the work order",
        schedules.loc[active, "Schedule ID"].tolist(),
        format_func=schedule_label,
    )
    work_order_schedule = schedules.loc[schedules["Schedule ID"].eq(work_order_schedule_id)].iloc[0]
    already_generated = preventive_work_order_exists(work_order_schedule_id)
    if already_generated:
        st.info("A preventive work order has already been generated for this schedule.", icon=":material/info:")
    elif st.button("Generate work order", icon=":material/add_task:", type="primary"):
        work_order_id = generate_preventive_work_order(work_order_schedule)
        if work_order_id:
            st.session_state["work_orders"] = load_work_orders()
            st.session_state["work_order_notice"] = f"{work_order_id} created from {work_order_schedule_id}."
            st.success(f"{work_order_id} created and assigned to {work_order_schedule['Assigned To']}.", icon=":material/check_circle:")
        else:
            st.info("A preventive work order has already been generated for this schedule.", icon=":material/info:")

with st.container(border=True):
    st.subheader(":material/checklist: Maintenance checklists")
    st.caption("Complete the steps for a scheduled task and save the checklist for the next technician or review.")
    selected_schedule_id = st.selectbox(
        "Select scheduled maintenance",
        schedules["Schedule ID"].tolist(),
        format_func=schedule_label,
    )
    selected_schedule = schedules.loc[schedules["Schedule ID"].eq(selected_schedule_id)].iloc[0]
    checklist = load_checklist(selected_schedule_id)
    if checklist.empty:
        checklist = default_checklist(selected_schedule["Maintenance Task"])
        st.info("A standard checklist has been prepared for this maintenance task. Mark its steps and save it.")

    completed_steps = int(checklist["Complete"].sum())
    st.progress(completed_steps / len(checklist), text=f"{completed_steps} of {len(checklist)} steps complete")
    edited_checklist = st.data_editor(
        checklist,
        hide_index=True,
        width="stretch",
        key=f"checklist_editor_{selected_schedule_id}",
        column_config={
            "Checklist item": st.column_config.TextColumn("Checklist step", width="large"),
            "Complete": st.column_config.CheckboxColumn("Complete"),
        },
    )
    if st.button("Save checklist", icon=":material/save:", type="primary", key="save_checklist"):
        save_checklist(selected_schedule_id, edited_checklist)
        st.success("Checklist progress saved.", icon=":material/check_circle:")
