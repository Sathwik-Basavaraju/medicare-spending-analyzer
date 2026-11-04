"""Streamlit dashboard for the Medicare spending analyzer (demo).

Run from the project root:
    streamlit run dashboard/app.py

Reads data/sample_providers.csv (anonymised) and
outputs/outliers.csv (review candidates only).
Outliers are review candidates, NOT findings of wrongdoing.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = ROOT / "data" / "sample_providers.csv"
OUTLIER_PATH = ROOT / "outputs" / "outliers.csv"


def main() -> None:
    st.title("Medicare Spending Variation Analyzer (Sample)")
    st.caption("Outliers are review candidates only, not findings of wrongdoing.")
    if not SAMPLE_PATH.exists():
        st.error("data/sample_providers.csv not found.")
        return
    df = pd.read_csv(SAMPLE_PATH)
    st.subheader("Median payment per beneficiary by specialty")
    med = df.groupby("specialty")["payment_per_bene"].median().sort_values(ascending=False).head(15)
    st.bar_chart(med)
    st.subheader("Median payment per beneficiary by state")
    med_state = df.groupby("state")["payment_per_bene"].median().sort_values(ascending=False).head(15)
    st.bar_chart(med_state)
    st.subheader("Payment per beneficiary vs beneficiaries (log scale)")
    st.scatter_chart(df, x="tot_benes", y="payment_per_bene")
    if OUTLIER_PATH.exists():
        out = pd.read_csv(OUTLIER_PATH)
        st.subheader(f"Outliers for review ({len(out)} providers)")
        st.dataframe(out[["provider_id", "specialty", "state", "tot_benes",
                          "payment_per_bene", "peer_median", "z"]].head(100))
    st.subheader("Sample data (first 100 rows, anonymised)")
    st.dataframe(df.head(100))


if __name__ == "__main__":
    main()
