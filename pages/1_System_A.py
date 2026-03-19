import os
import altair as alt
import streamlit as st
from common.data import load_credit_default, apply_group_filters

st.set_page_config(page_title="System A", layout="wide")
st.title("System A")

DATA_PATH = os.path.join("data", "default_of_credit_card_clients.xls")


@st.cache_data
def get_data():
    return load_credit_default(DATA_PATH)


df, trend_long = get_data()
alt.data_transformers.disable_max_rows()

# -------------------------
# session state for T1
# -------------------------
if "a_sex" not in st.session_state:
    st.session_state.a_sex = None
if "a_marriage" not in st.session_state:
    st.session_state.a_marriage = None
if "a_education" not in st.session_state:
    st.session_state.a_education = None

# =========================================================
# T1
# =========================================================
st.subheader("T1: Search and Select")

c1, c2, c3 = st.columns(3)

with c1:
    sex_options = [None] + sorted([x for x in df["sex"].dropna().unique().tolist()])
    st.session_state.a_sex = st.selectbox(
        "Sex",
        sex_options,
        index=sex_options.index(st.session_state.a_sex) if st.session_state.a_sex in sex_options else 0,
        format_func=lambda x: "All" if x is None else x,
        key="system_a_t4_sex"
    )

with c2:
    marriage_options = [None] + sorted([x for x in df["marriage"].dropna().unique().tolist()])
    st.session_state.a_marriage = st.selectbox(
        "Marriage",
        marriage_options,
        index=marriage_options.index(st.session_state.a_marriage) if st.session_state.a_marriage in marriage_options else 0,
        format_func=lambda x: "All" if x is None else x,
        key="system_a_t4_marriage"
    )

with c3:
    education_options = [None] + sorted([x for x in df["education"].dropna().unique().tolist()])
    st.session_state.a_education = st.selectbox(
        "Education",
        education_options,
        index=education_options.index(st.session_state.a_education) if st.session_state.a_education in education_options else 0,
        format_func=lambda x: "All" if x is None else x,
        key="system_a_t4_education"
    )

filtered_df = apply_group_filters(
    df,
    st.session_state.a_sex,
    st.session_state.a_marriage,
    st.session_state.a_education
)

filtered_trend = apply_group_filters(
    trend_long,
    st.session_state.a_sex,
    st.session_state.a_marriage,
    st.session_state.a_education
)

st.caption(
    f"Currently selected subset size: {len(filtered_df):,} | "
    f"Sex: {st.session_state.a_sex or 'All'} | "
    f"Marriage: {st.session_state.a_marriage or 'All'} | "
    f"Education: {st.session_state.a_education or 'All'}"
)

# =========================================================
# T2
# =========================================================
st.subheader("T2: Summarize and Compare")

st.markdown(
    "Compare the distribution of customers with **default payment next month = Yes** "
    "versus **No** across different credit limit ranges."
)

hist = (
    alt.Chart(filtered_df)
    .mark_bar(opacity=0.45)
    .encode(
        x=alt.X(
            "LIMIT_BAL:Q",
            bin=alt.Bin(maxbins=35),
            title="Credit Limit (New Taiwan Dollars)"
        ),
        y=alt.Y(
            "count():Q",
            title="Number of Customers"
        ),
        color=alt.Color(
            "default payment next month:N",
            title="Default Payment Next Month",
            scale=alt.Scale(
                domain=["No", "Yes"],
                range=["#4C78A8", "#E45756"]
            )
        ),
        tooltip=[
            alt.Tooltip("count():Q", title="Number of Customers"),
            alt.Tooltip("default payment next month:N", title="Default Payment Next Month")
        ]
    )
    .properties(
        height=320,
        title="Distribution of Credit Limit (LIMIT_BAL)"
    )
)

st.altair_chart(hist, width="stretch")

# =========================================================
# T3
# =========================================================
st.subheader("T3: Find Outliers")

risk_df = filtered_df[filtered_df["RISK_FLAG"]].copy()

if len(risk_df) > 2500:
    risk_df = risk_df.sample(2500, random_state=42).copy()

if len(risk_df) == 0:
    st.warning("No high-risk customers are available for outlier analysis under the current T1 selection.")
else:
    # Thresholds computed within the current high-risk subset
    bill_threshold = risk_df["BILL_MEAN"].quantile(0.75)
    pay_threshold = risk_df["PAY_MEAN"].quantile(0.25)

    # Outlier candidates: high average bill amount + low average payment amount
    risk_df["Outlier Candidate"] = (
        (risk_df["BILL_MEAN"] >= bill_threshold) &
        (risk_df["PAY_MEAN"] <= pay_threshold)
    ).map({True: "Yes", False: "No"})

    base = alt.Chart(risk_df)

    normal_points = (
        base.transform_filter(alt.datum["Outlier Candidate"] == "No")
        .mark_circle(size=55, opacity=0.45, color="#9E9E9E")
        .encode(
            x=alt.X("BILL_MEAN:Q", title="Average Bill Amount (X12-X17)"),
            y=alt.Y("PAY_MEAN:Q", title="Average Payment Amount (X18-X23)"),
            tooltip=[
                alt.Tooltip("ID:Q", title="Customer ID"),
                alt.Tooltip("sex:N", title="Sex"),
                alt.Tooltip("marriage:N", title="Marriage"),
                alt.Tooltip("education:N", title="Education"),
                alt.Tooltip("BILL_MEAN:Q", title="Average Bill Amount", format=".2f"),
                alt.Tooltip("PAY_MEAN:Q", title="Average Payment Amount", format=".2f"),
                alt.Tooltip("Outlier Candidate:N", title="Outlier Candidate"),
                alt.Tooltip("default payment next month:N", title="Default Payment Next Month")
            ]
        )
    )

    outlier_points = (
        base.transform_filter(alt.datum["Outlier Candidate"] == "Yes")
        .mark_circle(size=95, opacity=0.9, color="#E45756")
        .encode(
            x="BILL_MEAN:Q",
            y="PAY_MEAN:Q",
            tooltip=[
                alt.Tooltip("ID:Q", title="Customer ID"),
                alt.Tooltip("sex:N", title="Sex"),
                alt.Tooltip("marriage:N", title="Marriage"),
                alt.Tooltip("education:N", title="Education"),
                alt.Tooltip("BILL_MEAN:Q", title="Average Bill Amount", format=".2f"),
                alt.Tooltip("PAY_MEAN:Q", title="Average Payment Amount", format=".2f"),
                alt.Tooltip("Outlier Candidate:N", title="Outlier Candidate"),
                alt.Tooltip("default payment next month:N", title="Default Payment Next Month")
            ]
        )
    )

    bill_rule = alt.Chart(
        alt.Data(values=[{"bill_threshold": float(bill_threshold)}])
    ).mark_rule(strokeDash=[6, 4], color="#444").encode(
        x="bill_threshold:Q"
    )

    pay_rule = alt.Chart(
        alt.Data(values=[{"pay_threshold": float(pay_threshold)}])
    ).mark_rule(strokeDash=[6, 4], color="#444").encode(
        y="pay_threshold:Q"
    )

    outlier_rect = alt.Chart(
        alt.Data(values=[{
            "x1": float(bill_threshold),
            "x2": float(risk_df["BILL_MEAN"].max()),
            "y1": float(risk_df["PAY_MEAN"].min()),
            "y2": float(pay_threshold)
        }])
    ).mark_rect(opacity=0.08, color="#E45756").encode(
        x="x1:Q",
        x2="x2:Q",
        y="y1:Q",
        y2="y2:Q"
    )

    legend_df = alt.Data(values=[
        {"Category": "Regular High-Risk Customer", "x": 1, "y": 1, "color": "#9E9E9E"},
        {"Category": "Outlier Candidate", "x": 1, "y": 2, "color": "#E45756"}
    ])

    legend_chart = (
        alt.Chart(legend_df)
        .mark_point(filled=True, size=120)
        .encode(
            y=alt.Y("Category:N", axis=alt.Axis(title="")),
            x=alt.value(10),
            color=alt.Color(
                "Category:N",
                scale=alt.Scale(
                    domain=["Regular High-Risk Customer", "Outlier Candidate"],
                    range=["#9E9E9E", "#E45756"]
                ),
                legend=None
            )
        )
        .properties(width=220, height=80)
    )

    scatter = (
        (outlier_rect + normal_points + outlier_points + bill_rule + pay_rule)
        .properties(
            height=380,
            title="Outlier Identification Among High-Risk Customers"
        )
    )

    st.altair_chart(scatter, width="stretch")
    st.altair_chart(legend_chart, width="content")

    st.markdown(
        """
This chart only shows **high-risk customers**, defined as customers with at least one positive **PAY_X** value.

Each point represents one customer:  
- The x-axis shows the customer’s **average bill amount** across **X12-X17**
- The y-axis shows the customer’s **average payment amount** across **X18-X23**

The system uses two reference lines to define the **high bill amount** and **low payment amount** region.  
Customers located in the **high bill amount + low payment amount** area are treated as **outlier candidates**.

`default payment next month` is displayed only as supporting information and is **not used** to define outliers.
"""
    )

# =========================================================
# T4
# =========================================================
st.subheader("T4: Analyze Trends")

trend_t3 = filtered_trend[
    filtered_trend["PAY_STATUS_NUM"].isin([-1, 1, 2, 3, 4, 5, 6, 7, 8, 9])
].copy()

if len(trend_t3) == 0:
    st.warning("No repayment status records are available for T4 under the current T1 selection.")
else:
    trend_dist = (
        trend_t3.groupby(
            ["MONTH", "MONTH_ORDER", "PAY_STATUS_DESCRIPTION"],
            as_index=False
        )
        .size()
        .rename(columns={"size": "Count"})
    )

    stacked_bar = (
        alt.Chart(trend_dist)
        .mark_bar()
        .encode(
            x=alt.X(
                "MONTH:N",
                sort=["2005-04", "2005-05", "2005-06", "2005-07", "2005-08", "2005-09"],
                title="Month"
            ),
            y=alt.Y(
                "Count:Q",
                stack="normalize",
                title="Proportion"
            ),
            color=alt.Color(
                "PAY_STATUS_DESCRIPTION:N",
                title="Repayment Status"
            ),
            tooltip=[
                alt.Tooltip("MONTH:N", title="Month"),
                alt.Tooltip("PAY_STATUS_DESCRIPTION:N", title="Repayment Status"),
                alt.Tooltip("Count:Q", title="Number of Customers")
            ]
        )
        .properties(
            height=320,
            title="Repayment Pattern Over the Six Months Under the Current T1 Selection"
        )
    )

    st.altair_chart(stacked_bar, width="stretch")