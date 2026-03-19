import streamlit as st

st.set_page_config(page_title="IV Group Project - Multiview Systems", layout="wide")

st.title("IV Group Project — Multiview Visualisation (A/B/C)")
st.write(
    """
Use the left sidebar to open System A, B, or C pages.

- Each system is **multi-view** and supports **brushing & linking** (selection-driven filtering).
- System C additionally supports **generalised selection** (hierarchical abstraction).
"""
)
st.info("Go to: Sidebar → Pages → System A / System B / System C")