from pathlib import Path

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio


def apply_theme():
    """Load the shared visual theme on every Streamlit page."""
    css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    pio.templates["facilityops"] = go.layout.Template(
        layout=go.Layout(
            paper_bgcolor="rgba(21,36,66,0.86)",
            plot_bgcolor="rgba(12,25,50,0.70)",
            font={"family": "DM Sans, sans-serif", "color": "#edf3ff"},
            colorway=["#7c8cff", "#4de1d1", "#ff9b8e", "#ae7cf5", "#ffd166"],
            legend={"bgcolor": "rgba(0,0,0,0)", "font": {"color": "#edf3ff"}},
            xaxis={"gridcolor": "rgba(177,202,242,0.16)", "zerolinecolor": "rgba(177,202,242,0.22)"},
            yaxis={"gridcolor": "rgba(177,202,242,0.16)", "zerolinecolor": "rgba(177,202,242,0.22)"},
            margin={"l": 30, "r": 24, "t": 36, "b": 30},
        )
    )
    px.defaults.template = "facilityops"
