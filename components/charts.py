import plotly.express as px


def machine_type_chart(df):

    fig = px.pie(
        df,
        names="Type",
        hole=0.6,
        title="Machine Type Distribution"
    )

    fig.update_layout(height=430)

    return fig


def failure_chart(df):

    data = {
        "Failure": [
            "TWF",
            "HDF",
            "PWF",
            "OSF",
            "RNF"
        ],
        "Count": [
            df["TWF"].sum(),
            df["HDF"].sum(),
            df["PWF"].sum(),
            df["OSF"].sum(),
            df["RNF"].sum()
        ]
    }

    fig = px.bar(
        data,
        x="Failure",
        y="Count",
        color="Failure",
        title="Failure Type Distribution"
    )

    fig.update_layout(height=430)

    return fig