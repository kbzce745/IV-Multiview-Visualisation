import os
import altair as alt
import streamlit as st
from common.data import load_credit_default
import pandas as pd
import numpy as np

st.set_page_config(page_title="System B", layout="wide")
st.title("System B")

DATA_PATH = os.path.join("data", "default_of_credit_card_clients.xls")


@st.cache_data
def get_data():
    return load_credit_default(DATA_PATH)


df, trend_long = get_data()
alt.data_transformers.disable_max_rows()

# =========================================================
# T1: Search and Select
# =========================================================
st.subheader("T1: Search and Select")

group_dim_label = st.selectbox(
    "Choose a background variable for group comparison",
    ["All", "Sex", "Marriage", "Education"],
    key="system_b_group_dim"
)

group_dim_map = {
    "Sex": "sex",
    "Marriage": "marriage",
    "Education": "education"
}

if group_dim_label == "All":
    group_dim = None
    selected_group = "All"
    filtered_df = df.copy()
    filtered_trend = trend_long.copy()
    st.caption("Currently showing all customers without grouping by background variable.")

else:
    group_dim = group_dim_map[group_dim_label]

    group_counts = (
        df.groupby(group_dim, as_index=False)
        .size()
        .rename(columns={"size": "Customer Count"})
    )

    group_bar = (
        alt.Chart(group_counts)
        .mark_bar(color="#4C78A8")
        .encode(
            y=alt.Y(f"{group_dim}:N", sort="-x", title="Customer Group"),
            x=alt.X("Customer Count:Q", title="Number of Customers"),
            tooltip=[
                alt.Tooltip(f"{group_dim}:N", title="Customer Group"),
                alt.Tooltip("Customer Count:Q", title="Number of Customers")
            ]
        )
        .properties(
            height=220,
            title=f"Group Size Comparison by {group_dim_label}"
        )
    )

    st.altair_chart(group_bar, width="stretch")

    group_options = ["All"] + sorted(group_counts[group_dim].dropna().tolist())

    selected_group = st.radio(
        f"Choose one {group_dim_label} group for T2, T3, and T4 below",
        group_options,
        horizontal=True,
        key=f"system_b_selected_group_{group_dim}"
    )

    if selected_group == "All":
        filtered_df = df.copy()
        filtered_trend = trend_long.copy()
    else:
        filtered_df = df[df[group_dim] == selected_group].copy()
        filtered_trend = trend_long[trend_long[group_dim] == selected_group].copy()

st.caption(
    f"Current selection: {group_dim_label} = {selected_group} | "
    f"Subset size: {len(filtered_df):,}"
)

# =========================================================
# T2: Summarize and Compare
# =========================================================
st.subheader("T2: Summarize and Compare")

boxplot = (
    alt.Chart(filtered_df)
    .mark_boxplot(extent="min-max")
    .encode(
        x=alt.X(
            "default payment next month:N",
            title="Default Payment Next Month",
            sort=["No", "Yes"]
        ),
        y=alt.Y("LIMIT_BAL:Q", title="Credit Limit (New Taiwan Dollars)"),
        color=alt.Color(
            "default payment next month:N",
            title="Default Payment Next Month",
            scale=alt.Scale(
                domain=["No", "Yes"],
                range=["#4C78A8", "#E45756"]
            ),
            legend=None
        )
    )
    .properties(
        height=500,
        title="Distribution of LIMIT_BAL by Default Payment Next Month"
    )
)

st.altair_chart(boxplot, width="stretch")

# =========================================================
# T3: Find outliers
# =========================================================
st.subheader("T3: Find Outliers")

pay_cols = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]

filtered_df_t2 = filtered_df.copy()
filtered_df_t2["RISK_FLAG_SUBSET"] = filtered_df_t2[pay_cols].gt(0).any(axis=1)

risk_df = filtered_df_t2[filtered_df_t2["RISK_FLAG_SUBSET"]].copy()

if len(risk_df) < 20:
    st.warning("There are too few high-risk customers in the current subset to identify outliers reliably.")
else:
    # Thresholds based on the current high-risk subset
    bill_threshold = float(risk_df["BILL_MEAN"].quantile(0.75))
    pay_threshold = float(risk_df["PAY_MEAN"].quantile(0.25))

    # Reduce the number of bins for clearer color contrast
    n_bins = 20

    x_min = float(risk_df["BILL_MEAN"].min())
    x_max = float(risk_df["BILL_MEAN"].max())
    y_min = 0.0
    y_max = float(risk_df["PAY_MEAN"].max())

    if x_min == x_max:
        x_max = x_min + 1
    if y_min == y_max:
        y_max = y_min + 1

    # Use numeric bin boundaries directly to avoid interval/category compatibility issues
    x_edges = np.linspace(x_min, x_max, n_bins + 1)
    y_edges = np.linspace(y_min, y_max, n_bins + 1)

    risk_df["x_bin"] = pd.cut(
        risk_df["BILL_MEAN"],
        bins=x_edges,
        include_lowest=True
    )
    risk_df["y_bin"] = pd.cut(
        risk_df["PAY_MEAN"],
        bins=y_edges,
        include_lowest=True
    )

    heat_df = (
        risk_df.dropna(subset=["x_bin", "y_bin"])
        .groupby(["x_bin", "y_bin"], observed=False)
        .size()
        .reset_index(name="Customer Count")
    )

    # Expand interval boundaries and cast explicitly
    heat_df["x1"] = heat_df["x_bin"].map(lambda v: float(v.left)).astype("float64")
    heat_df["x2"] = heat_df["x_bin"].map(lambda v: float(v.right)).astype("float64")
    heat_df["y1"] = heat_df["y_bin"].map(lambda v: float(v.left)).astype("float64")
    heat_df["y2"] = heat_df["y_bin"].map(lambda v: float(v.right)).astype("float64")

    # Keep only bins with customers
    heat_df = heat_df[heat_df["Customer Count"] > 0].copy()

    heat_df["Outlier Region Bin"] = (
        (heat_df["x1"] >= bill_threshold) &
        (heat_df["y2"] <= pay_threshold)
    )

    # Main heatmap
    heatmap = (
        alt.Chart(heat_df)
        .mark_rect(opacity=1)
        .encode(
            x=alt.X("x1:Q", title="Average Bill Amount (X12-X17)"),
            x2="x2:Q",
            y=alt.Y("y1:Q", title="Average Payment Amount (X18-X23)"),
            y2="y2:Q",
            color=alt.Color(
                "Customer Count:Q",
                title="Number of Customers",
                scale=alt.Scale(
                    scheme="blues",
                    domainMin=1
                )
            ),
            tooltip=[
                alt.Tooltip("Customer Count:Q", title="Number of Customers"),
                alt.Tooltip("x1:Q", title="Bill Range Lower Bound", format=",.0f"),
                alt.Tooltip("x2:Q", title="Bill Range Upper Bound", format=",.0f"),
                alt.Tooltip("y1:Q", title="Payment Range Lower Bound", format=",.0f"),
                alt.Tooltip("y2:Q", title="Payment Range Upper Bound", format=",.0f"),
            ]
        )
        .properties(
            height=380,
            title="2D Distribution of Bill Amount and Payment Amount Among High-Risk Customers"
        )
    )

    # Background for the outlier region
    outlier_region = (
        alt.Chart(pd.DataFrame([{
            "x1": bill_threshold,
            "x2": x_max,
            "y1": 0.0,
            "y2": pay_threshold
        }]))
        .mark_rect(opacity=0.28, color="#E45756")
        .encode(
            x="x1:Q",
            x2="x2:Q",
            y="y1:Q",
            y2="y2:Q"
        )
    )

    # Highlight bins that actually fall into the outlier region
    anomaly_bins = (
        alt.Chart(heat_df[heat_df["Outlier Region Bin"]])
        .mark_rect(
            fillOpacity=0.0,
            stroke="#E45756",
            strokeWidth=2.5
        )
        .encode(
            x="x1:Q",
            x2="x2:Q",
            y="y1:Q",
            y2="y2:Q",
            tooltip=[
                alt.Tooltip("Customer Count:Q", title="Customers in Outlier Region"),
                alt.Tooltip("x1:Q", title="Bill Range Lower Bound", format=",.0f"),
                alt.Tooltip("x2:Q", title="Bill Range Upper Bound", format=",.0f"),
                alt.Tooltip("y1:Q", title="Payment Range Lower Bound", format=",.0f"),
                alt.Tooltip("y2:Q", title="Payment Range Upper Bound", format=",.0f"),
            ]
        )
    )

    bill_rule = (
        alt.Chart(pd.DataFrame([{"bill": bill_threshold}]))
        .mark_rule(strokeDash=[6, 4], color="#E45756")
        .encode(x="bill:Q")
    )

    pay_rule = (
        alt.Chart(pd.DataFrame([{"pay": pay_threshold}]))
        .mark_rule(strokeDash=[6, 4], color="#E45756")
        .encode(y="pay:Q")
    )

    chart = outlier_region + heatmap + anomaly_bins + bill_rule + pay_rule
    st.altair_chart(chart, use_container_width=True)

    # Table of specific outlier customers
    anomaly_df = risk_df[
        (risk_df["BILL_MEAN"] >= bill_threshold) &
        (risk_df["PAY_MEAN"] <= pay_threshold)
    ].copy()

    st.markdown(f"""
This chart only shows **high-risk customers within the currently selected group**,  
defined as customers with **at least one PAY_X > 0**.

The x-axis shows the customer’s **average bill amount across X12-X17**,  
and the y-axis shows the customer’s **average payment amount across X18-X23**.

The dashed reference lines indicate the thresholds for the current high-risk subset:

- High bill amount ≥ **{bill_threshold:,.0f}**
- Low payment amount ≤ **{pay_threshold:,.0f}**

The light red region in the lower-right corner represents: **high bill amount + low payment amount**.  
The red outlined rectangles highlight the bins that actually fall into this outlier region.  
The number of currently identified potential outlier customers is: **{len(anomaly_df)}**
""")

    if len(anomaly_df) > 0:
        st.markdown("**Details of Potential Outlier Customers**")

        show_cols = ["BILL_MEAN", "PAY_MEAN", "default payment next month", "sex", "marriage", "education"]
        if "ID" in anomaly_df.columns:
            show_cols = ["ID"] + show_cols

        st.dataframe(
            anomaly_df[show_cols].sort_values(
                ["BILL_MEAN", "PAY_MEAN"],
                ascending=[False, True]
            ),
            use_container_width=True
        )
    else:
        st.info("No customers fall into the outlier region under the current thresholds.")

# =========================================================
# T4: Analyze Trends
# =========================================================
st.subheader("T4: Analyze Trends")

trend_t3 = filtered_trend[
    filtered_trend["PAY_STATUS_NUM"].isin([-1, 1, 2, 3, 4, 5, 6, 7, 8, 9])
].copy()

month_order = ["2005-04", "2005-05", "2005-06", "2005-07", "2005-08", "2005-09"]

if len(trend_t3) == 0:
    st.warning("There are no repayment status records available for T4 in the current subset.")
else:
    if group_dim is None:
        trend_counts = (
            trend_t3.groupby(["MONTH", "MONTH_ORDER", "PAY_STATUS_DESCRIPTION"], as_index=False)
            .size()
            .rename(columns={"size": "Count"})
        )
        trend_counts["Total Count"] = trend_counts.groupby(["MONTH"])["Count"].transform("sum")
        trend_counts["Proportion"] = trend_counts["Count"] / trend_counts["Total Count"]

        heatmap_t3 = (
            alt.Chart(trend_counts)
            .mark_rect()
            .encode(
                x=alt.X("MONTH:N", sort=month_order, title="Month"),
                y=alt.Y("PAY_STATUS_DESCRIPTION:N", title="Repayment Status"),
                color=alt.Color("Proportion:Q", title="Proportion"),
                tooltip=[
                    alt.Tooltip("MONTH:N", title="Month"),
                    alt.Tooltip("PAY_STATUS_DESCRIPTION:N", title="Repayment Status"),
                    alt.Tooltip("Count:Q", title="Number of Customers"),
                    alt.Tooltip("Proportion:Q", title="Proportion", format=".2%")
                ]
            )
            .properties(
                height=360,
                title="Six-Month Repayment Pattern Heatmap for All Customers"
            )
        )

    else:
        trend_counts = (
            trend_t3.groupby([group_dim, "MONTH", "MONTH_ORDER", "PAY_STATUS_DESCRIPTION"], as_index=False)
            .size()
            .rename(columns={"size": "Count"})
        )
        trend_counts["Total Count"] = trend_counts.groupby([group_dim, "MONTH"])["Count"].transform("sum")
        trend_counts["Proportion"] = trend_counts["Count"] / trend_counts["Total Count"]

        if selected_group == "All":
            heatmap_t3 = (
                alt.Chart(trend_counts)
                .mark_rect()
                .encode(
                    x=alt.X("MONTH:N", sort=month_order, title="Month"),
                    y=alt.Y("PAY_STATUS_DESCRIPTION:N", title="Repayment Status"),
                    color=alt.Color("Proportion:Q", title="Proportion"),
                    column=alt.Column(f"{group_dim}:N", title="Customer Group"),
                    tooltip=[
                        alt.Tooltip(f"{group_dim}:N", title="Customer Group"),
                        alt.Tooltip("MONTH:N", title="Month"),
                        alt.Tooltip("PAY_STATUS_DESCRIPTION:N", title="Repayment Status"),
                        alt.Tooltip("Count:Q", title="Number of Customers"),
                        alt.Tooltip("Proportion:Q", title="Proportion", format=".2%")
                    ]
                )
                .properties(
                    height=320,
                    title=f"Six-Month Repayment Pattern Heatmap by {group_dim_label}"
                )
            )
        else:
            trend_counts_single = trend_counts[trend_counts[group_dim] == selected_group].copy()

            heatmap_t3 = (
                alt.Chart(trend_counts_single)
                .mark_rect()
                .encode(
                    x=alt.X("MONTH:N", sort=month_order, title="Month"),
                    y=alt.Y("PAY_STATUS_DESCRIPTION:N", title="Repayment Status"),
                    color=alt.Color("Proportion:Q", title="Proportion"),
                    tooltip=[
                        alt.Tooltip(f"{group_dim}:N", title="Customer Group"),
                        alt.Tooltip("MONTH:N", title="Month"),
                        alt.Tooltip("PAY_STATUS_DESCRIPTION:N", title="Repayment Status"),
                        alt.Tooltip("Count:Q", title="Number of Customers"),
                        alt.Tooltip("Proportion:Q", title="Proportion", format=".2%")
                    ]
                )
                .properties(
                    height=360,
                    title=f"Six-Month Repayment Pattern Heatmap for {selected_group}"
                )
            )

    st.altair_chart(heatmap_t3, width="stretch")