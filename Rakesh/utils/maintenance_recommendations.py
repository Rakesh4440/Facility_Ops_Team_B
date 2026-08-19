"""Explainable maintenance recommendations derived from current operational data."""

from __future__ import annotations

from datetime import date

import pandas as pd


RECOMMENDATION_COLUMNS = ["Priority", "Recommendation", "Why now", "Owner", "Due date"]


def build_maintenance_recommendations(
    schedules: pd.DataFrame,
    work_orders: pd.DataFrame,
    today: date | None = None,
) -> pd.DataFrame:
    """Prioritize the maintenance actions that should receive attention next."""
    today = today or date.today()
    recommendations: list[dict[str, str]] = []
    schedule_data = schedules.copy()
    schedule_data["Due date"] = pd.to_datetime(
        schedule_data["Next Due Date"], errors="coerce"
    ).dt.date
    active_schedules = schedule_data[schedule_data["Active"].eq("Yes")]

    overdue = active_schedules[active_schedules["Due date"].lt(today)].sort_values("Due date")
    for _, schedule in overdue.iterrows():
        days_overdue = (today - schedule["Due date"]).days
        priority = "Critical" if days_overdue >= 7 else "High"
        recommendations.append(
            {
                "Priority": priority,
                "Recommendation": f"Complete {schedule['Schedule ID']} — {schedule['Maintenance Task']}.",
                "Why now": f"Preventive maintenance is {days_overdue} day(s) overdue for {schedule['Product ID']}.",
                "Owner": schedule["Assigned To"],
                "Due date": schedule["Next Due Date"],
            }
        )

    upcoming = active_schedules[
        active_schedules["Due date"].ge(today)
        & active_schedules["Due date"].le(today + pd.Timedelta(days=7))
    ].sort_values("Due date")
    for _, schedule in upcoming.iterrows():
        days_until_due = (schedule["Due date"] - today).days
        priority = "High" if days_until_due <= 2 else "Medium"
        recommendations.append(
            {
                "Priority": priority,
                "Recommendation": f"Prepare {schedule['Schedule ID']} — {schedule['Maintenance Task']}.",
                "Why now": f"Due in {days_until_due} day(s); verify parts, access, and technician availability.",
                "Owner": schedule["Assigned To"],
                "Due date": schedule["Next Due Date"],
            }
        )

    open_orders = work_orders[work_orders["Status"].isin(["Open", "In Progress"])].copy()
    open_orders["Due date"] = pd.to_datetime(open_orders["Due Date"], errors="coerce").dt.date
    delayed_orders = open_orders[open_orders["Due date"].lt(today)].sort_values("Due date")
    for _, order in delayed_orders.iterrows():
        days_overdue = (today - order["Due date"]).days
        recommendations.append(
            {
                "Priority": "Critical" if order["Priority"] == "High" else "High",
                "Recommendation": f"Escalate work order {order['ID']} — {order['Issue']}.",
                "Why now": f"The {order['Status'].lower()} work order is {days_overdue} day(s) past due.",
                "Owner": order["Assigned To"],
                "Due date": order["Due Date"],
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "Priority": "Low",
                "Recommendation": "Continue the preventive maintenance plan as scheduled.",
                "Why now": "No overdue schedules, near-term maintenance tasks, or delayed work orders were found.",
                "Owner": "Maintenance team",
                "Due date": "—",
            }
        )

    priority_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    result = pd.DataFrame(recommendations, columns=RECOMMENDATION_COLUMNS)
    return result.sort_values(
        "Priority", key=lambda priorities: priorities.map(priority_rank), kind="stable"
    ).reset_index(drop=True)
