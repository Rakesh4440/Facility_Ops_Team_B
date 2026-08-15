import streamlit as st

from components.theme import apply_theme
from utils.auth import require_auth
from utils.maintenance_history import load_maintenance_history, record_completed_work_order
from utils.work_order_pdf import build_work_order_pdf
from utils.work_orders import load_work_orders, save_work_orders
from utils.auth import get_current_user

try:
    st.set_page_config(page_title="Work orders", page_icon=":material/build:", layout="wide")
except Exception:
    pass
apply_theme()




if "work_orders" not in st.session_state:
    st.session_state["work_orders"] = load_work_orders()
st.session_state.setdefault("work_order_notice", None)

st.title(":material/assignment: Work order management")
st.caption("Track open maintenance work, keep assignments clear, and update progress in one place.")

notice = st.session_state.pop("work_order_notice", None)
if notice:
    st.success(notice, icon=":material/check_circle:")

work_orders = st.session_state["work_orders"]
statuses = ["Open", "In Progress", "Completed"]
kpis = st.columns(4)
kpis[0].metric(":material/list_alt: Total orders", len(work_orders))
kpis[1].metric(":material/task_alt: Open", int((work_orders["Status"] == "Open").sum()))
kpis[2].metric(":material/pending_actions: In progress", int((work_orders["Status"] == "In Progress").sum()))
kpis[3].metric(":material/verified: Completed", int((work_orders["Status"] == "Completed").sum()))

with st.container(border=True):
    st.subheader(":material/filter_alt: Find work orders")
    st.caption("Filter by machine Product ID or focus on a specific work-order status.")
    search_col, status_col = st.columns(2)
    with search_col:
        product_search = st.text_input("Search by Product ID", placeholder="For example, M14860")
    with status_col:
        status_filter = st.selectbox("Filter by status", ["All", *statuses])

filtered_orders = work_orders.copy()
if product_search:
    filtered_orders = filtered_orders[
        filtered_orders["Product ID"].str.contains(product_search, case=False, na=False)
    ]
if status_filter != "All":
    filtered_orders = filtered_orders[filtered_orders["Status"] == status_filter]

st.subheader(":material/table_chart: Work orders")
st.caption(f"Showing {len(filtered_orders)} of {len(work_orders)} work orders")
st.dataframe(
    filtered_orders,
    hide_index=True,
    height=260,
    column_config={
        "ID": st.column_config.TextColumn("Work order", pinned=True),
        "Product ID": st.column_config.TextColumn("Product ID"),
        "Machine Type": st.column_config.TextColumn("Machine type"),
        "Assigned To": st.column_config.TextColumn("Assigned to"),
        "Due Date": st.column_config.TextColumn("Due date"),
    },
)

from utils.auth import get_current_user

user = get_current_user()
is_admin = user and user.get("role", "").lower() == "admin"

if is_admin:
    update_col, download_col, delete_col = st.columns(3)
else:
    update_col, download_col = st.columns(2)

order_ids = work_orders["ID"].tolist()

with update_col:
    with st.container(border=True):
        st.subheader(":material/edit_note: Update work order")
        st.caption("Move a task through the maintenance workflow.")
        selected_order = st.selectbox("Select work order", order_ids, key="update_order")
        new_status = st.selectbox("New status", statuses)
        completion_notes = st.text_area(
            "Completion notes",
            placeholder="Optional: parts replaced, inspection result, or follow-up required.",
        )
        if st.button("Update status", icon=":material/save:", type="primary"):
            selected_work_order = st.session_state["work_orders"].loc[
                st.session_state["work_orders"]["ID"] == selected_order
            ].iloc[0]
            st.session_state["work_orders"].loc[
                st.session_state["work_orders"]["ID"] == selected_order, "Status"
            ] = new_status
            save_work_orders(st.session_state["work_orders"])
            if new_status == "Completed":
                recorded = record_completed_work_order(selected_work_order, completion_notes)
                history_message = " Maintenance history recorded." if recorded else " Maintenance history already exists."
            else:
                history_message = ""
            st.session_state["work_order_notice"] = f"{selected_order} updated to {new_status}.{history_message}"
            st.rerun()

with download_col:
    with st.container(border=True):
        st.subheader(":material/picture_as_pdf: Download work order")
        st.caption("Create a PDF handoff sheet to share with the assigned technician or maintenance team.")
        download_order = st.selectbox("Select work order", order_ids, key="download_order")
        work_order_for_download = work_orders.loc[work_orders["ID"] == download_order].iloc[0]
        st.download_button(
            "Download work order PDF",
            data=build_work_order_pdf(work_order_for_download.to_dict()),
            file_name=f"{download_order}_FacilityOps_Work_Order.pdf",
            mime="application/pdf",
            icon=":material/download:",
            type="primary",
        )

if is_admin:
    with delete_col:
        with st.container(border=True):
            st.subheader(":material/delete_outline: Delete work order")
            st.caption("Removal is saved permanently in the local work-order list.")
            delete_order = st.selectbox("Select work order", order_ids, key="delete_order")
            confirm_delete = st.checkbox("I confirm that this work order should be deleted.")
            if st.button("Delete work order", icon=":material/delete:"):
                if not confirm_delete:
                    st.warning("Confirm deletion before removing the work order.", icon=":material/warning:")
                else:
                    st.session_state["work_orders"] = st.session_state["work_orders"].loc[
                        st.session_state["work_orders"]["ID"] != delete_order
                    ].reset_index(drop=True)
                    save_work_orders(st.session_state["work_orders"])
                    st.session_state["work_order_notice"] = f"{delete_order} deleted."
                    st.rerun()


with st.container(border=True):
    st.subheader(":material/history: Maintenance history")
    st.caption("Completed maintenance work is retained here for operational review and traceability.")
    maintenance_history = load_maintenance_history()
    if maintenance_history.empty:
        st.info("No completed maintenance has been recorded yet.", icon=":material/history:")
    else:
        st.dataframe(
            maintenance_history,
            hide_index=True,
            width="stretch",
            column_config={
                "Work order": st.column_config.TextColumn("Work order", pinned=True),
                "Completed on": st.column_config.DateColumn("Completed on", format="DD MMM YYYY"),
            },
        )
