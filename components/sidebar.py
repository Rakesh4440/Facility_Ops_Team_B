import streamlit as st

def sidebar_filters(df):

    st.sidebar.title("⚙ Dashboard Filters")

    machine = st.sidebar.multiselect(
        "Machine Type",
        options=sorted(df["Type"].unique()),
        default=sorted(df["Type"].unique())
    )

    failure = st.sidebar.multiselect(
        "Machine Failure",
        options=sorted(df["Machine failure"].unique()),
        default=sorted(df["Machine failure"].unique())
    )

    df = df[
        (df["Type"].isin(machine))
        &
        (df["Machine failure"].isin(failure))
    ]

    return df