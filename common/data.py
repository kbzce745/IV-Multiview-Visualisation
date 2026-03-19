import os
import pandas as pd

RENAME_MAP = {
    "X1": "LIMIT_BAL",
    "X2": "SEX",
    "X3": "EDUCATION",
    "X4": "MARRIAGE",
    "X5": "AGE",
    "X6": "PAY_0",
    "X7": "PAY_2",
    "X8": "PAY_3",
    "X9": "PAY_4",
    "X10": "PAY_5",
    "X11": "PAY_6",
    "X12": "BILL_AMT1",
    "X13": "BILL_AMT2",
    "X14": "BILL_AMT3",
    "X15": "BILL_AMT4",
    "X16": "BILL_AMT5",
    "X17": "BILL_AMT6",
    "X18": "PAY_AMT1",
    "X19": "PAY_AMT2",
    "X20": "PAY_AMT3",
    "X21": "PAY_AMT4",
    "X22": "PAY_AMT5",
    "X23": "PAY_AMT6",
}

PAY_STATUS_COLS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
BILL_COLS = ["BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6"]
PAY_AMT_COLS = ["PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6"]

SEX_LABELS = {
    1: "Male",
    2: "Female"
}

EDUCATION_LABELS = {
    1: "Graduate school",
    2: "University",
    3: "High school",
    4: "Others"
}

MARRIAGE_LABELS = {
    1: "Married",
    2: "Single",
    3: "Others"
}

Y_LABELS = {
    0: "No",
    1: "Yes"
}


def pay_status_label(x):
    if pd.isna(x):
        return ""
    x = int(x)
    if x == -1:
        return "pay duly"
    if 1 <= x <= 8:
        return f"payment delay for {x} months"
    if x == 9:
        return "payment delay for nine months and above"
    return str(x)


def _read_excel_auto(path: str, header=None) -> pd.DataFrame:
    ext = os.path.splitext(path.lower())[1]
    if ext == ".xls":
        return pd.read_excel(path, header=header, engine="xlrd")
    return pd.read_excel(path, header=header, engine="openpyxl")


def load_credit_default(path: str):
    raw = _read_excel_auto(path, header=None)

    header_row_idx = None
    for i in range(min(10, len(raw))):
        row = raw.iloc[i].astype(str).tolist()
        if "ID" in row:
            header_row_idx = i
            break
    if header_row_idx is None:
        header_row_idx = 1

    df = _read_excel_auto(path, header=header_row_idx)

    if "default payment next month" in df.columns:
        df = df.rename(columns={"default payment next month": "Y"})
    if "Y" not in df.columns and "y" in df.columns:
        df = df.rename(columns={"y": "Y"})

    df = df.rename(columns={k: v for k, v in RENAME_MAP.items() if k in df.columns})
    df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")].copy()

    if "Y" in df.columns:
        df["Y"] = pd.to_numeric(df["Y"], errors="coerce").fillna(0).astype(int)

    if "ID" in df.columns:
        df = df.drop_duplicates(subset=["ID"])

    df["sex"] = df["SEX"].map(SEX_LABELS)
    df["education"] = df["EDUCATION"].map(EDUCATION_LABELS)
    df["marriage"] = df["MARRIAGE"].map(MARRIAGE_LABELS)
    df["default payment next month"] = df["Y"].map(Y_LABELS)

    df["BILL_MEAN"] = df[BILL_COLS].mean(axis=1)
    df["PAY_MEAN"] = df[PAY_AMT_COLS].mean(axis=1)
    df["RISK_FLAG"] = (df[PAY_STATUS_COLS] > 0).any(axis=1)
    df["PAY_DELAY_COUNT"] = (df[PAY_STATUS_COLS] > 0).sum(axis=1)

    trend_long = df[
        ["ID", "sex", "marriage", "education", "default payment next month"] + PAY_STATUS_COLS
    ].melt(
        id_vars=["ID", "sex", "marriage", "education", "default payment next month"],
        value_vars=PAY_STATUS_COLS,
        var_name="PAY_MONTH",
        value_name="PAY_STATUS_NUM"
    )

    month_label_map = {
        "PAY_6": "2005-04",
        "PAY_5": "2005-05",
        "PAY_4": "2005-06",
        "PAY_3": "2005-07",
        "PAY_2": "2005-08",
        "PAY_0": "2005-09",
    }

    month_order_map = {
        "PAY_6": 1,
        "PAY_5": 2,
        "PAY_4": 3,
        "PAY_3": 4,
        "PAY_2": 5,
        "PAY_0": 6,
    }

    trend_long["MONTH"] = trend_long["PAY_MONTH"].map(month_label_map)
    trend_long["MONTH_ORDER"] = trend_long["PAY_MONTH"].map(month_order_map)
    trend_long["PAY_STATUS_DESCRIPTION"] = trend_long["PAY_STATUS_NUM"].apply(pay_status_label)

    return df, trend_long


def apply_group_filters(df: pd.DataFrame, sex=None, marriage=None, education=None) -> pd.DataFrame:
    out = df.copy()
    if sex is not None:
        out = out[out["sex"] == sex]
    if marriage is not None:
        out = out[out["marriage"] == marriage]
    if education is not None:
        out = out[out["education"] == education]
    return out