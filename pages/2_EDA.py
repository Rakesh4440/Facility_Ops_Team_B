import streamlit as st
import pandas as pd
import plotly.express as px
from components.theme import apply_theme
from utils.auth import require_auth

# ---------------------------------------
# Page Config
# ---------------------------------------
try:
    st.set_page_config(
        page_title="EDA",
        page_icon="📊",
        layout="wide"
    )
except Exception:
    pass
apply_theme()


df = pd.read_csv("data/ai4i2020.csv")

# ---------------------------------------
# Title
# ---------------------------------------
st.markdown('<div class="hero-eyebrow">Data intelligence</div>', unsafe_allow_html=True)
st.title("Exploratory Data Analysis")
st.caption("A structured view of data quality, distributions, and machine-failure relationships.")
st.success("Dataset loaded successfully")
# ---------------------------------------
st.subheader("ℹ Dataset Information")

left, right = st.columns(2)

with left:
    st.write("### Data Types")

    dtype = pd.DataFrame({
        "Column": df.columns,
        "Datatype": df.dtypes.astype(str)
    })

    st.dataframe(dtype, use_container_width=True)

with right:

    summary = pd.DataFrame({

        "Property":[
            "Rows",
            "Columns",
            "Memory (KB)",
            "Numeric Columns",
            "Categorical Columns"
        ],

        "Value":[
            df.shape[0],
            df.shape[1],
            round(df.memory_usage().sum()/1024,2),
            len(df.select_dtypes("number").columns),
            len(df.select_dtypes("object").columns)
        ]
    })

    st.write("### Summary")

    st.dataframe(summary,use_container_width=True)

st.divider()

# ---------------------------------------
# Missing Values
# ---------------------------------------
st.subheader("❌ Missing Value Analysis")

missing = df.isnull().sum()

missing_df = pd.DataFrame({
    "Column":missing.index,
    "Missing Values":missing.values
})

st.dataframe(missing_df,use_container_width=True)

fig = px.bar(
    missing_df,
    x="Column",
    y="Missing Values",
    color="Missing Values",
    title="Missing Values in Dataset"
)

st.plotly_chart(fig,use_container_width=True)

st.divider()

# ---------------------------------------
# Descriptive Statistics
# ---------------------------------------
st.subheader("📈 Descriptive Statistics")

st.dataframe(df.describe(),use_container_width=True)

st.divider()

# ---------------------------------------
# Correlation Heatmap
# ---------------------------------------
st.subheader("🔥 Correlation Heatmap")

corr = df.select_dtypes(include="number").corr()

fig = px.imshow(
    corr,
    text_auto=True,
    color_continuous_scale="RdBu_r",
    aspect="auto"
)

st.plotly_chart(fig,use_container_width=True)

st.divider()

# ---------------------------------------
# Histogram
# ---------------------------------------
st.subheader("📊 Histogram")

numeric = df.select_dtypes(include="number").columns

column = st.selectbox(
    "Select Numerical Column",
    numeric
)

fig = px.histogram(
    df,
    x=column,
    nbins=30,
    color_discrete_sequence=["royalblue"]
)

st.plotly_chart(fig,use_container_width=True)

st.divider()

# ---------------------------------------
# Box Plot
# ---------------------------------------
st.subheader("📦 Box Plot")

column = st.selectbox(
    "Choose Column",
    numeric,
    key="box"
)

fig = px.box(
    df,
    y=column,
    color_discrete_sequence=["orange"]
)

st.plotly_chart(fig,use_container_width=True)

st.divider()

# ---------------------------------------
# Machine Type Distribution
# ---------------------------------------
st.subheader("🏭 Machine Type Distribution")

fig = px.pie(
    df,
    names="Type",
    title="Machine Types"
)

st.plotly_chart(fig,use_container_width=True)

st.divider()


# ---------------------------------------
# Machine Failure Distribution
# ---------------------------------------
st.subheader("⚠ Machine Failure Distribution")

fig = px.histogram(
    df,
    x="Machine failure",
    color="Machine failure"
)

st.plotly_chart(fig,use_container_width=True)

st.divider()

# ---------------------------------------
# Temperature Scatter
# ---------------------------------------
st.subheader("🌡 Air vs Process Temperature")

fig = px.scatter(
    df,
    x="Air temperature [K]",
    y="Process temperature [K]",
    color="Machine failure"
)

st.plotly_chart(fig,use_container_width=True)

st.divider()

# ---------------------------------------
# Torque Analysis
# ---------------------------------------
st.subheader("⚙ Torque Analysis")

fig = px.histogram(
    df,
    x="Torque [Nm]",
    nbins=30
)

st.plotly_chart(fig,use_container_width=True)
