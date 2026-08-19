from pathlib import Path

import pandas as pd
import streamlit as st

from utils.ai_assistant import (
    OllamaModelNotFoundError,
    OllamaServerUnavailableError,
    generate_ai_report,
)
from utils.work_orders import (
    WORK_ORDER_COLUMNS,
    load_work_orders,
    next_work_order_id,
    save_work_orders,
)
from utils.work_order_pdf import build_work_order_pdf
from utils.ai_report_pdf import build_ai_report_pdf


try:
    st.set_page_config(page_title="Machine explorer", page_icon=":material/manage_search:", layout="wide")
except Exception:
    pass





@st.cache_data
def load_machine_data() -> pd.DataFrame:
    data_path = Path(__file__).resolve().parents[1] / "data" / "ai4i2020.csv"
    return pd.read_csv(data_path)


df = load_machine_data()
st.session_state.setdefault("selected_machine_id", None)
st.session_state.setdefault("ai_report", None)
if "work_orders" not in st.session_state:
    st.session_state["work_orders"] = load_work_orders()
st.session_state.setdefault("work_order_notice", None)
st.session_state.setdefault("created_work_order", None)

st.title(":material/manage_search: Machine explorer")
st.caption("Find a machine, review its live operating signals, and generate a focused maintenance brief.")

with st.sidebar:
    st.subheader("Machine data filters")
    machine_types = st.multiselect(
        "Machine Type",
        options=["L", "M", "H"],
        default=["L", "M", "H"],
        key="explorer_machine_types",
    )
    machine_status = st.multiselect(
        "Machine Status",
        options=["Healthy", "Failed"],
        default=["Healthy", "Failed"],
        key="explorer_machine_status",
    )

status_values = []
if "Healthy" in machine_status:
    status_values.append(0)
if "Failed" in machine_status:
    status_values.append(1)

filtered_df = df[
    df["Type"].isin(machine_types) & df["Machine failure"].isin(status_values)
]

with st.expander(":material/database: Browse machine data", expanded=False):
    st.caption(f"Showing {len(filtered_df):,} of {len(df):,} machines")
    st.dataframe(
        filtered_df,
        hide_index=True,
        height=420,
        column_config={
            "Air temperature [K]": st.column_config.NumberColumn("Air Temperature", format="%.1f K"),
            "Process temperature [K]": st.column_config.NumberColumn("Process Temperature", format="%.1f K"),
            "Rotational speed [rpm]": st.column_config.NumberColumn("Rotational Speed", format="%d rpm"),
            "Torque [Nm]": st.column_config.NumberColumn("Torque", format="%.1f Nm"),
            "Tool wear [min]": st.column_config.NumberColumn("Tool Wear", format="%d min"),
        },
    )

with st.container(border=True):
    st.markdown("#### :material/search: Find a machine")
    st.caption("Use the Product ID from the dataset, such as M14860.")
    with st.form("machine_search_form"):
        product_id = st.text_input("Enter Product ID", placeholder="For example, M14860")
        search_submitted = st.form_submit_button("Search machine", icon=":material/search:")

if search_submitted:
    normalized_id = product_id.strip().upper()
    match = df[df["Product ID"].str.upper() == normalized_id]
    if match.empty:
        st.session_state.selected_machine_id = None
        st.session_state.ai_report = None
        st.error("No machine found for that Product ID.")
    else:
        st.session_state.selected_machine_id = match.iloc[0]["Product ID"]
        st.session_state.ai_report = None

selected_machine_id = st.session_state.selected_machine_id
if selected_machine_id:
    machine = df.loc[df["Product ID"] == selected_machine_id].iloc[0]
    st.success(f"Machine {machine['Product ID']} loaded successfully.", icon=":material/check_circle:")

    with st.container(border=True):
        st.subheader(":material/precision_manufacturing: Machine information")
        left, right = st.columns(2)
        with left:
            st.markdown(f":blue-badge[Product ID] **{machine['Product ID']}**")
            st.markdown(f":violet-badge[Machine type] **{machine['Type']}**")
            st.write(f":material/air: **Air temperature:** {machine['Air temperature [K]']:.1f} K")
            st.write(f":material/thermostat: **Process temperature:** {machine['Process temperature [K]']:.1f} K")
        with right:
            st.write(f":material/speed: **Rotational speed:** {machine['Rotational speed [rpm]']:,} rpm")
            st.write(f":material/tune: **Torque:** {machine['Torque [Nm]']:.1f} Nm")
            st.write(f":material/construction: **Tool wear:** {machine['Tool wear [min]']} min")
            status_badge = ":red-badge[Failure detected]" if machine["Machine failure"] else ":green-badge[No failure detected]"
            st.markdown(f":material/verified_user: **Machine status:** {status_badge}")

    st.subheader(":material/health_and_safety: Health status")
    if machine["Machine failure"]:
        st.error("Critical — a machine failure has been detected. Maintenance action is required.", icon=":material/error:")
    elif machine["Tool wear [min]"] >= 180:
        st.warning("Needs attention — tool wear is elevated; schedule an inspection.", icon=":material/warning:")
    else:
        st.success("Healthy — no machine failure is detected in the selected record.", icon=":material/verified:")

    st.subheader(":material/sensors: Live sensor values")
    metric_cols = st.columns(3)
    metric_cols[0].metric(":material/speed: RPM", f"{machine['Rotational speed [rpm]']:,} rpm")
    metric_cols[1].metric(":material/tune: Torque", f"{machine['Torque [Nm]']:.1f} Nm")
    metric_cols[2].metric(":material/construction: Tool wear", f"{machine['Tool wear [min]']} min")
    metric_cols = st.columns(2)
    metric_cols[0].metric(":material/air: Air temperature", f"{machine['Air temperature [K]']:.1f} K")
    metric_cols[1].metric(":material/thermostat: Process temperature", f"{machine['Process temperature [K]']:.1f} K")

    st.subheader(":material/notification_important: Failure analysis")
    failures = [
        ("Tool Wear Failure", "TWF"),
        ("Heat Dissipation Failure", "HDF"),
        ("Power Failure", "PWF"),
        ("Overstrain Failure", "OSF"),
        ("Random Failure", "RNF"),
    ]
    with st.container(border=True):
        failure_left, failure_right = st.columns(2)
        for index, (label, flag) in enumerate(failures):
            target = failure_left if index < 3 else failure_right
            with target:
                result = ":red-badge[Detected]" if machine[flag] else ":green-badge[Clear]"
                st.markdown(f":material/{'error' if machine[flag] else 'check_circle'}: **{label}:** {result}")

    st.subheader(":material/smart_toy: AI maintenance assistant")
    st.caption("Generate a complete maintenance report with sensor context, risk, and recommended actions.")
    if st.button("Analyze machine", icon=":material/auto_awesome:", type="primary"):
        progress = st.progress(0, text="Preparing machine data...")
        progress.progress(25, text="Preparing machine data...")
        progress.progress(50, text="Generating complete AI maintenance report...")

        try:
            st.session_state.ai_report = {
                "product_id": machine["Product ID"],
                "content": generate_ai_report(machine.to_dict()),
            }
            progress.progress(100, text="AI report ready.")
        except OllamaServerUnavailableError:
            st.session_state.ai_report = None
            st.error("Ollama server is not running.")
        except OllamaModelNotFoundError:
            st.session_state.ai_report = None
            st.error("llama3.2 model not found.")
        except Exception as exc:
            st.session_state.ai_report = None
            st.error(f"Unable to generate the AI report: {exc}")
        finally:
            progress.empty()

    report = st.session_state.ai_report
    if report and report["product_id"] == machine["Product ID"]:
        st.success("Report Generated Successfully", icon=":material/check_circle:")
        with st.container(border=True):
            st.markdown(report["content"])
            st.download_button(
                "Download report",
                data=build_ai_report_pdf(report["content"]),
                file_name=f"{machine['Product ID']}_ai_maintenance_report.pdf",
                mime="application/pdf",
                icon=":material/download:",
                type="primary",
            )

        if machine["Machine failure"]:
            st.divider()
            st.subheader(":material/add_task: Create maintenance work order")
            st.caption(
                f"A failure is detected for **{machine['Product ID']}**. Create a reactive task "
                "(corrective, breakdown, emergency, inspection, or safety check). "
                "Planned preventive jobs are created from Maintenance schedules, not here. "
                "Saved work orders appear in Work order management."
            )
            with st.form("create_machine_work_order", border=True):
                issue = st.selectbox(
                    "Maintenance issue",
                    [
                        "Corrective maintenance",
                        "Breakdown repair",
                        "Emergency repair",
                        "Inspection",
                        "Safety check",
                    ],
                )
                details = st.text_area(
                    "Work details",
                    placeholder="Describe the maintenance task recommended by the AI analysis.",
                )
                priority_col, technician_col = st.columns(2)
                with priority_col:
                    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                with technician_col:
                    technician = st.text_input("Assign technician", placeholder="For example, A. Sharma")
                due_date = st.date_input("Due date", format="YYYY/MM/DD")
                status = st.selectbox("Status", ["Open", "In Progress", "Completed"])
                create_order = st.form_submit_button(
                    "Create work order", icon=":material/add_task:", type="primary"
                )

            if create_order:
                if not details.strip():
                    st.error("Add work details before creating the work order.", icon=":material/error:")
                elif not technician.strip():
                    st.error("Assign a technician before creating the work order.", icon=":material/error:")
                else:
                    work_orders = st.session_state["work_orders"]
                    work_order_id = next_work_order_id(work_orders)
                    work_order = pd.DataFrame(
                        [[
                            work_order_id,
                            machine["Product ID"],
                            machine["Type"],
                            f"{issue}: {details.strip()}",
                            priority,
                            technician.strip(),
                            due_date.isoformat(),
                            status,
                        ]],
                        columns=WORK_ORDER_COLUMNS,
                    )
                    st.session_state["work_orders"] = pd.concat(
                        [work_orders, work_order], ignore_index=True
                    )
                    save_work_orders(st.session_state["work_orders"])
                    st.session_state["created_work_order"] = work_order.iloc[0].to_dict()
                    st.session_state["work_order_notice"] = (
                        f"{work_order_id} created for {machine['Product ID']}."
                    )
                    st.success(
                        f"{work_order_id} created successfully for {machine['Product ID']}.",
                        icon=":material/check_circle:",
                    )

            created_order = st.session_state["created_work_order"]
            if created_order and created_order["Product ID"] == machine["Product ID"]:
                st.download_button(
                    "Download this work order as PDF",
                    data=build_work_order_pdf(created_order),
                    file_name=f"{created_order['ID']}_maintenance_work_order.pdf",
                    mime="application/pdf",
                    icon=":material/picture_as_pdf:",
                    type="primary",
                )
