import os
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from common.data import load_credit_default

st.set_page_config(page_title="System C", layout="wide")
st.title("System C")

DATA_PATH = os.path.join("data", "default_of_credit_card_clients.xls")


@st.cache_data
def get_data():
    return load_credit_default(DATA_PATH)


df, trend_long = get_data()
alt.data_transformers.disable_max_rows()

# =========================================================
# 0. Data preprocessing: clean missing values and build
# hierarchical semantic groups
# =========================================================
df = df.copy()
trend_long = trend_long.copy()

cat_cols = ["education", "marriage", "sex"]

for c in cat_cols:
    df[c] = df[c].astype("string").fillna("Unknown").replace("<NA>", "Unknown").replace("nan", "Unknown")
    trend_long[c] = trend_long[c].astype("string").fillna("Unknown").replace("<NA>", "Unknown").replace("nan", "Unknown")

df["CLIENT_ID"] = np.arange(1, len(df) + 1).astype(str)

df["SEG_L0"] = df["education"] + " | " + df["marriage"] + " | " + df["sex"]
df["SEG_L1"] = df["education"] + " | " + df["marriage"]
df["SEG_L2"] = df["education"]
df["SEG_L3"] = "All Customers"

trend_long["SEG_L0"] = trend_long["education"] + " | " + trend_long["marriage"] + " | " + trend_long["sex"]
trend_long["SEG_L1"] = trend_long["education"] + " | " + trend_long["marriage"]
trend_long["SEG_L2"] = trend_long["education"]
trend_long["SEG_L3"] = "All Customers"

# Only allow leaf groups with sufficient sample size
MIN_LEAF_SIZE = 80

leaf_counts = (
    df.groupby(["SEG_L0", "SEG_L1", "SEG_L2"], as_index=False)
    .size()
    .rename(columns={"size": "Customer Count"})
    .sort_values("Customer Count", ascending=False)
)

eligible_leafs = leaf_counts[leaf_counts["Customer Count"] >= MIN_LEAF_SIZE].copy()

if len(eligible_leafs) == 0:
    st.error("No leaf group satisfies the minimum sample size requirement. Please reduce MIN_LEAF_SIZE.")
    st.stop()

leaf_options = eligible_leafs["SEG_L0"].tolist()
leaf_to_l1 = dict(zip(eligible_leafs["SEG_L0"], eligible_leafs["SEG_L1"]))
leaf_to_l2 = dict(zip(eligible_leafs["SEG_L0"], eligible_leafs["SEG_L2"]))

# =========================================================
# 1. Session state: keep the current semantic level
# level: L0 -> L1 -> L2 -> L3
# =========================================================
if "system_c_level" not in st.session_state:
    st.session_state.system_c_level = "L0"

if "system_c_l0" not in st.session_state:
    st.session_state.system_c_l0 = leaf_options[0]

if "system_c_l1" not in st.session_state:
    st.session_state.system_c_l1 = leaf_to_l1[leaf_options[0]]

if "system_c_l2" not in st.session_state:
    st.session_state.system_c_l2 = leaf_to_l2[leaf_options[0]]


def set_leaf_selection(l0_value: str):
    st.session_state.system_c_level = "L0"
    st.session_state.system_c_l0 = l0_value
    st.session_state.system_c_l1 = leaf_to_l1[l0_value]
    st.session_state.system_c_l2 = leaf_to_l2[l0_value]


def generalise_one_level():
    level = st.session_state.system_c_level
    if level == "L0":
        st.session_state.system_c_level = "L1"
    elif level == "L1":
        st.session_state.system_c_level = "L2"
    elif level == "L2":
        st.session_state.system_c_level = "L3"


def specialise_one_level():
    level = st.session_state.system_c_level
    if level == "L3":
        st.session_state.system_c_level = "L2"
    elif level == "L2":
        st.session_state.system_c_level = "L1"
    elif level == "L1":
        st.session_state.system_c_level = "L0"


def reset_selection():
    set_leaf_selection(leaf_options[0])


def get_current_subset(df_in, trend_in):
    level = st.session_state.system_c_level

    if level == "L0":
        key = st.session_state.system_c_l0
        sub_df = df_in[df_in["SEG_L0"] == key].copy()
        sub_trend = trend_in[trend_in["SEG_L0"] == key].copy()
        label = f"L0 Leaf Group: {key}"

    elif level == "L1":
        key = st.session_state.system_c_l1
        sub_df = df_in[df_in["SEG_L1"] == key].copy()
        sub_trend = trend_in[trend_in["SEG_L1"] == key].copy()
        label = f"L1 Education × Marriage: {key}"

    elif level == "L2":
        key = st.session_state.system_c_l2
        sub_df = df_in[df_in["SEG_L2"] == key].copy()
        sub_trend = trend_in[trend_in["SEG_L2"] == key].copy()
        label = f"L2 Education: {key}"

    else:
        sub_df = df_in.copy()
        sub_trend = trend_in.copy()
        label = "L3 All Customers"

    return sub_df, sub_trend, label


current_df, current_trend, current_label = get_current_subset(df, trend_long)

# =========================================================
# 2. T1: Generalised Selection
# =========================================================
st.subheader("T1: Generalised Selection")

left, right = st.columns([1.0, 2.2])

with left:
    selected_leaf = st.selectbox(
        "Choose a leaf group as the starting point (only groups with sufficient sample size are shown)",
        options=leaf_options,
        index=leaf_options.index(st.session_state.system_c_l0) if st.session_state.system_c_l0 in leaf_options else 0,
        format_func=lambda x: f"{x} (n={int(eligible_leafs.loc[eligible_leafs['SEG_L0'] == x, 'Customer Count'].iloc[0])})"
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Set Current"):
            set_leaf_selection(selected_leaf)
    with c2:
        if st.button("Generalise ↑"):
            generalise_one_level()
    with c3:
        if st.button("Specialise ↓"):
            specialise_one_level()
    with c4:
        if st.button("Reset"):
            reset_selection()

with right:
    display_counts = eligible_leafs.copy()

    if st.session_state.system_c_level == "L0":
        display_counts["Status"] = np.where(
            display_counts["SEG_L0"] == st.session_state.system_c_l0, "Current Leaf", "Other"
        )
    elif st.session_state.system_c_level == "L1":
        display_counts["Status"] = np.where(
            display_counts["SEG_L1"] == st.session_state.system_c_l1, "Covered by Current Parent", "Other"
        )
    elif st.session_state.system_c_level == "L2":
        display_counts["Status"] = np.where(
            display_counts["SEG_L2"] == st.session_state.system_c_l2, "Covered by Current Parent", "Other"
        )
    else:
        display_counts["Status"] = "All"

    bar_t4 = (
        alt.Chart(display_counts.head(20))
        .mark_bar()
        .encode(
            y=alt.Y("SEG_L0:N", sort="-x", title="Leaf Group (Top 20)"),
            x=alt.X("Customer Count:Q", title="Number of Customers"),
            color=alt.Color(
                "Status:N",
                scale=alt.Scale(
                    domain=["Current Leaf", "Covered by Current Parent", "All", "Other"],
                    range=["#E45756", "#F58518", "#4C78A8", "#D3D3D3"]
                ),
                legend=alt.Legend(title="Current Semantic Selection")
            ),
            tooltip=[
                alt.Tooltip("SEG_L0:N", title="Leaf Group"),
                alt.Tooltip("SEG_L1:N", title="L1"),
                alt.Tooltip("SEG_L2:N", title="L2"),
                alt.Tooltip("Customer Count:Q", title="Number of Customers")
            ]
        )
        .properties(height=380, title="Leaf Group Distribution in the Semantic Hierarchy (Top 20)")
    )

    st.altair_chart(bar_t4, width="stretch")

# Recompute the current subset after T4 interaction
current_df, current_trend, current_label = get_current_subset(df, trend_long)

st.markdown(
    f"""
**Current Hierarchy Path**  
`{st.session_state.system_c_l0}`  
→ `{st.session_state.system_c_l1}`  
→ `{st.session_state.system_c_l2}`  
→ `All Customers`
"""
)

st.info(f"{current_label} | Sample Size: {len(current_df):,}")

# =========================================================
# 3. Overview: Brushing and Linking
# =========================================================
st.subheader("Overview: Brushing and Linking")

overview_df = current_df.copy()
if len(overview_df) > 2500:
    overview_df = overview_df.sample(2500, random_state=42)

brush = alt.selection_interval()

scatter = (
    alt.Chart(overview_df)
    .mark_circle(size=50, opacity=0.65)
    .encode(
        x=alt.X("BILL_MEAN:Q", title="Average Bill Amount (X12-X17)"),
        y=alt.Y("PAY_MEAN:Q", title="Average Payment Amount (X18-X23)"),
        color=alt.Color(
            "default payment next month:N",
            title="Default Payment Next Month",
            scale=alt.Scale(domain=["No", "Yes"], range=["#4C78A8", "#E45756"])
        ),
        tooltip=[
            alt.Tooltip("education:N", title="Education"),
            alt.Tooltip("marriage:N", title="Marriage"),
            alt.Tooltip("sex:N", title="Sex"),
            alt.Tooltip("LIMIT_BAL:Q", title="Credit Limit"),
            alt.Tooltip("BILL_MEAN:Q", title="Average Bill Amount", format=",.0f"),
            alt.Tooltip("PAY_MEAN:Q", title="Average Payment Amount", format=",.0f"),
        ]
    )
    .add_params(brush)
    .properties(height=320, title="Customer Scatterplot")
)

linked_hist = (
    alt.Chart(overview_df)
    .transform_filter(brush)
    .mark_bar()
    .encode(
        x=alt.X("LIMIT_BAL:Q", bin=alt.Bin(maxbins=25), title="Credit Limit (LIMIT_BAL)"),
        y=alt.Y("count():Q", title="Number of Customers"),
        tooltip=[alt.Tooltip("count():Q", title="Number of Customers")]
    )
    .properties(height=320, title="Credit Limit Distribution of Brushed Customers")
)

st.altair_chart(scatter | linked_hist, width="stretch")

# =========================================================
# 4. T2: Summarize and Compare
# changed to density instead of boxplot
# =========================================================
st.subheader("T2: Summarize and Compare")

t1_classes = current_df["default payment next month"].dropna().unique().tolist()

if len(t1_classes) >= 2:
    density = (
        alt.Chart(current_df)
        .transform_density(
            "LIMIT_BAL",
            as_=["LIMIT_BAL", "density"],
            groupby=["default payment next month"]
        )
        .mark_area(opacity=0.45)
        .encode(
            x=alt.X("LIMIT_BAL:Q", title="Credit Limit (LIMIT_BAL)"),
            y=alt.Y("density:Q", title="Density"),
            color=alt.Color(
                "default payment next month:N",
                title="Default Payment Next Month",
                scale=alt.Scale(domain=["No", "Yes"], range=["#4C78A8", "#E45756"])
            ),
            tooltip=[
                alt.Tooltip("default payment next month:N", title="Default Payment Next Month")
            ]
        )
        .properties(height=320, title="Density Comparison of Credit Limit Under the Current Semantic Selection")
    )
    st.altair_chart(density, width="stretch")
else:
    fallback_hist = (
        alt.Chart(current_df)
        .mark_bar()
        .encode(
            x=alt.X("LIMIT_BAL:Q", bin=alt.Bin(maxbins=25), title="Credit Limit (LIMIT_BAL)"),
            y=alt.Y("count():Q", title="Number of Customers"),
        )
        .properties(height=320, title="Credit Limit Distribution Under the Current Semantic Selection")
    )
    st.altair_chart(fallback_hist, width="stretch")
    st.caption("Only one default class is present in the current subset, so a single-group distribution view is shown instead of a comparison view.")

# =========================================================
# T3: Find outliers
# Implementation: anomaly-score ranking bar chart
# different from A's scatter and B's heatmap
# =========================================================
st.subheader("T3: Find Outliers")

pay_cols = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]

t2_df = current_df.copy()
t2_df["RISK_FLAG_SUBSET"] = t2_df[pay_cols].gt(0).any(axis=1)
risk_df = t2_df[t2_df["RISK_FLAG_SUBSET"]].copy()

if len(risk_df) < 20:
    st.warning("There are too few high-risk customers under the current semantic selection to identify outliers reliably. Try generalising first.")
else:
    bill_med = risk_df["BILL_MEAN"].median()
    bill_iqr = risk_df["BILL_MEAN"].quantile(0.75) - risk_df["BILL_MEAN"].quantile(0.25)
    pay_med = risk_df["PAY_MEAN"].median()
    pay_iqr = risk_df["PAY_MEAN"].quantile(0.75) - risk_df["PAY_MEAN"].quantile(0.25)

    bill_iqr = bill_iqr if bill_iqr != 0 else 1
    pay_iqr = pay_iqr if pay_iqr != 0 else 1

    risk_df["bill_score"] = (risk_df["BILL_MEAN"] - bill_med) / bill_iqr
    risk_df["low_pay_score"] = (pay_med - risk_df["PAY_MEAN"]) / pay_iqr
    risk_df["anomaly_score"] = risk_df["bill_score"] + risk_df["low_pay_score"]

    top_n = min(20, len(risk_df))
    ranked_df = risk_df.nlargest(top_n, "anomaly_score").copy()

    if "ID" not in ranked_df.columns:
        ranked_df["ID"] = ranked_df.index.astype(str)

    ranked_df["Customer Label"] = ranked_df["ID"].astype(str)

    rank_chart = (
        alt.Chart(ranked_df)
        .mark_bar()
        .encode(
            y=alt.Y(
                "Customer Label:N",
                sort="-x",
                title="Customer (Top anomaly score)"
            ),
            x=alt.X(
                "anomaly_score:Q",
                title="Anomaly Score"
            ),
            color=alt.Color(
                "default payment next month:N",
                title="Default Payment Next Month",
                scale=alt.Scale(domain=["No", "Yes"], range=["#4C78A8", "#E45756"])
            ),
            tooltip=[
                alt.Tooltip("ID:N", title="Customer ID"),
                alt.Tooltip("education:N", title="Education"),
                alt.Tooltip("marriage:N", title="Marriage"),
                alt.Tooltip("sex:N", title="Sex"),
                alt.Tooltip("BILL_MEAN:Q", title="Average Bill Amount", format=",.0f"),
                alt.Tooltip("PAY_MEAN:Q", title="Average Payment Amount", format=",.0f"),
                alt.Tooltip("anomaly_score:Q", title="Anomaly Score", format=".2f"),
                alt.Tooltip("default payment next month:N", title="Default Payment Next Month")
            ]
        )
        .properties(
            height=420,
            title="Ranking of Customers with the Highest Anomaly Scores Under the Current Semantic Selection"
        )
    )

    st.altair_chart(rank_chart, width="stretch")

    st.markdown("""
This view no longer shows a two-dimensional spatial distribution.  
Instead, it directly ranks high-risk customers under the current semantic selection by **anomaly score**.

The anomaly score considers two aspects at the same time:
- Higher bill amount leads to a higher score
- Lower payment amount leads to a higher score

This view is therefore better suited to answering:  
**"Which customers deserve the highest priority attention at the current level?"**
""")

# =========================================================
# T4: Analyze Trends
# =========================================================
st.subheader("T4: Analyze Trends")

trend_t3 = current_trend.copy()

if len(trend_t3) == 0:
    st.warning("No trend records are available under the current semantic selection.")
else:
    def map_status(v):
        if pd.isna(v):
            return "Unknown"
        if v <= 0:
            return "On Time / Early"
        elif v == 1:
            return "1 Month Delay"
        else:
            return "2+ Months Delay"

    trend_t3["Status Level"] = trend_t3["PAY_STATUS_NUM"].apply(map_status)

    month_order = ["2005-04", "2005-05", "2005-06", "2005-07", "2005-08", "2005-09"]

    trend_summary = (
        trend_t3.groupby(["MONTH", "MONTH_ORDER", "Status Level"], as_index=False)
        .size()
        .rename(columns={"size": "Count"})
    )

    trend_summary["Total Count"] = trend_summary.groupby("MONTH")["Count"].transform("sum")
    trend_summary["Proportion"] = trend_summary["Count"] / trend_summary["Total Count"]

    line_chart = (
        alt.Chart(trend_summary)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "MONTH:N",
                sort=month_order,
                title="Month"
            ),
            y=alt.Y(
                "Proportion:Q",
                title="Proportion",
                axis=alt.Axis(format="%")
            ),
            color=alt.Color(
                "Status Level:N",
                title="Repayment Status Level",
                scale=alt.Scale(
                    domain=["On Time / Early", "1 Month Delay", "2+ Months Delay", "Unknown"],
                    range=["#4C78A8", "#F58518", "#E45756", "#BDBDBD"]
                )
            ),
            tooltip=[
                alt.Tooltip("MONTH:N", title="Month"),
                alt.Tooltip("Status Level:N", title="Status Level"),
                alt.Tooltip("Count:Q", title="Number of Customers"),
                alt.Tooltip("Proportion:Q", title="Proportion", format=".2%")
            ]
        )
        .properties(
            height=340,
            title="Monthly Change in Repayment Status Proportions Under the Current Semantic Selection"
        )
    )

    st.altair_chart(line_chart, width="stretch")

    st.markdown("""
This view aggregates repayment statuses into a few higher-level categories and compares how their proportions change over the six months.

So this T3 focuses more on:
- which status category is increasing
- which status category is decreasing
- whether there is a persistent deterioration or recovery trend under the current semantic level
""")