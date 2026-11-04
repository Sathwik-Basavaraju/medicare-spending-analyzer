"""Medicare spending variation analysis (DuckDB + pandas + matplotlib).

Usage:
    python3 src/analyze.py --input data/sample_providers.csv

Peer benchmarking follows sql/peer_benchmark.sql exactly:
  - peer group = specialty, minimum 30 providers per group
  - metric = payment_per_bene (total Medicare payment / beneficiaries)
  - outlier = z > 2.0 vs specialty peer median/std AND tot_benes >= 100
  - OUTLIERS ARE REVIEW CANDIDATES ONLY, not findings of wrongdoing.

Outputs: outputs/metrics.json, outputs/outliers.csv,
outputs/specialty_summary.csv, outputs/state_summary.csv,
outputs/charts/*.png
"""

import argparse
import json
import pathlib

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/sample_providers.csv")
    ap.add_argument("--out", default="outputs")
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    (out / "charts").mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"CREATE TABLE providers AS SELECT * FROM read_csv('{args.input}')")
    peer = con.execute("""
        SELECT specialty, COUNT(*) AS n_providers,
               MEDIAN(payment_per_bene) AS peer_median,
               STDDEV(payment_per_bene) AS peer_std
        FROM providers GROUP BY specialty HAVING COUNT(*) >= 30
    """).df()
    bench = con.execute("""
        SELECT p.*, peer.peer_median, peer.peer_std,
               (p.payment_per_bene - peer.peer_median) / NULLIF(peer.peer_std, 0) AS z,
               p.payment_per_bene / NULLIF(peer.peer_median, 0) AS ratio_to_median
        FROM providers p JOIN peer ON p.specialty = peer.specialty
    """).df()
    outliers = bench[(bench["z"] > 2.0) & (bench["tot_benes"] >= 100)].sort_values("z", ascending=False)
    spec = con.execute("""
        SELECT specialty, COUNT(*) AS n_providers,
               MEDIAN(payment_per_bene) AS median_payment_per_bene,
               MEDIAN(payment_per_service) AS median_payment_per_service,
               SUM(tot_payment) AS total_payment, SUM(tot_benes) AS total_benes
        FROM providers GROUP BY specialty ORDER BY median_payment_per_bene DESC
    """).df()
    state = con.execute("""
        SELECT state, COUNT(*) AS n_providers,
               MEDIAN(payment_per_bene) AS median_payment_per_bene,
               SUM(tot_payment) AS total_payment, SUM(tot_benes) AS total_benes
        FROM providers GROUP BY state ORDER BY median_payment_per_bene DESC
    """).df()
    bench.to_csv(out / "provider_benchmark.csv", index=False)
    outliers.to_csv(out / "outliers.csv", index=False)
    spec.to_csv(out / "specialty_summary.csv", index=False)
    state.to_csv(out / "state_summary.csv", index=False)

    # Charts
    top_spec = spec.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top_spec["specialty"], top_spec["median_payment_per_bene"])
    ax.set_xlabel("Median Medicare payment per beneficiary ($)")
    ax.set_title("Median payment per beneficiary by specialty (top 15, sample)")
    fig.tight_layout(); fig.savefig(out / "charts" / "median_by_specialty.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(bench["payment_per_bene"].clip(upper=bench["payment_per_bene"].quantile(0.99)), bins=40)
    ax.set_xlabel("Payment per beneficiary ($) — clipped at 99th percentile for display")
    ax.set_ylabel("Providers"); ax.set_title("Distribution of payment per beneficiary (sample)")
    fig.tight_layout(); fig.savefig(out / "charts" / "payment_per_bene_distribution.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 6))
    is_out = bench["provider_id"].isin(outliers["provider_id"])
    ax.scatter(bench.loc[~is_out, "tot_benes"], bench.loc[~is_out, "payment_per_bene"], s=8, alpha=0.4, label="Not flagged")
    ax.scatter(bench.loc[is_out, "tot_benes"], bench.loc[is_out, "payment_per_bene"], s=30, label="Outlier (review candidate)")
    ax.set_xscale("log"); ax.set_xlabel("Beneficiaries (log scale)"); ax.set_ylabel("Payment per beneficiary ($)")
    ax.set_title("Outliers vs payment per beneficiary (sample)"); ax.legend()
    fig.tight_layout(); fig.savefig(out / "charts" / "outlier_scatter.png", dpi=150); plt.close(fig)

    top_state = state.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top_state["state"], top_state["median_payment_per_bene"])
    ax.set_xlabel("Median payment per beneficiary ($)")
    ax.set_title("Median payment per beneficiary by state (top 15, sample)")
    fig.tight_layout(); fig.savefig(out / "charts" / "median_by_state.png", dpi=150); plt.close(fig)

    metrics = {
        "input_file": args.input,
        "input_rows": int(pd.read_csv(args.input).shape[0]),
        "providers_benchmarked_specialty_n_ge_30": int(len(bench)),
        "specialties_in_sample": int(pd.read_csv(args.input)["specialty"].nunique()),
        "states_in_sample": int(pd.read_csv(args.input)["state"].nunique()),
        "outlier_definition": "z > 2.0 vs specialty peer median/std (specialty groups with n>=30) AND tot_benes >= 100",
        "outliers_n": int(len(outliers)),
        "outliers_share_of_benchmarked": float(len(outliers) / len(bench)) if len(bench) else 0.0,
        "outliers_by_specialty": outliers["specialty"].value_counts().to_dict(),
        "outliers_by_state": outliers["state"].value_counts().to_dict(),
        "median_payment_per_bene_all": float(pd.read_csv(args.input)["payment_per_bene"].median()),
        "median_payment_per_service_all": float(pd.read_csv(args.input)["payment_per_service"].median()),
        "total_payment_sample": float(pd.read_csv(args.input)["tot_payment"].sum()),
        "total_benes_sample": float(pd.read_csv(args.input)["tot_benes"].sum()),
        "disclaimer": "Outliers are review candidates only, not findings of wrongdoing. Payment differences can reflect case mix, service mix, geography, and risk, which this peer-median method only partly adjusts for (see README.md).",
        "charts": ["charts/median_by_specialty.png", "charts/payment_per_bene_distribution.png",
                   "charts/outlier_scatter.png", "charts/median_by_state.png"],
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps({k: metrics[k] for k in ["input_rows", "providers_benchmarked_specialty_n_ge_30", "outliers_n", "specialties_in_sample", "states_in_sample"]}, indent=2))
    print(f"Wrote {out / 'metrics.json'}, {out / 'outliers.csv'}")


if __name__ == "__main__":
    main()
