import streamlit as st
import pandas as pd
import plotly.express as px
from components.theme import apply_theme
from utils.auth import require_auth

try:
    st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
except Exception:
    pass
apply_theme()


# Load Dataset
df = pd.read_csv("data/ai4i2020.csv")


st.title("FacilityOps Dashboard")
st.caption("Filter machine groups and review the signals that affect operational reliability.")

# ---------------- Sidebar ----------------
st.sidebar.markdown("## Dashboard filters")
st.sidebar.caption("Refine the operational view")

machine = st.sidebar.multiselect(
    "Machine Type",
    df["Type"].unique(),
    default=df["Type"].unique()
)

failure = st.sidebar.selectbox(
    "Machine Failure",
    ["All", 0, 1]
)

if failure != "All":
    df = df[df["Machine failure"] == failure]

df = df[df["Type"].isin(machine)]

# ---------------- KPI Cards ----------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Machines", len(df))
c2.metric("Failures", int(df["Machine failure"].sum()))
c3.metric("Avg Air Temp", round(df["Air temperature [K]"].mean(),2))
c4.metric("Avg Torque", round(df["Torque [Nm]"].mean(),2))

st.divider()

# ---------------- Charts ----------------
left, right = st.columns(2)

with left:
    st.subheader("Machine Type")
    fig = px.pie(df, names="Type")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Failure Distribution")
    fig = px.histogram(df, x="Machine failure", color="Machine failure")
    st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Air Temperature")
    fig = px.histogram(df, x="Air temperature [K]", nbins=30)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Torque")
    fig = px.histogram(df, x="Torque [Nm]", nbins=30)
    st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Air vs Process Temperature")
    fig = px.scatter(
        df,
        x="Air temperature [K]",
        y="Process temperature [K]",
        color="Type"
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Tool Wear")
    fig = px.box(
        df,
        x="Type",
        y="Tool wear [min]",
        color="Type"
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Failure Reasons")

failure_df = pd.DataFrame({
    "Failure Type":["TWF","HDF","PWF","OSF","RNF"],
    "Count":[
        df["TWF"].sum(),
        df["HDF"].sum(),
        df["PWF"].sum(),
        df["OSF"].sum(),
        df["RNF"].sum()
    ]
})

fig = px.bar(
    failure_df,
    x="Failure Type",
    y="Count",
    color="Failure Type"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Dataset")

st.dataframe(df, use_container_width=True)
