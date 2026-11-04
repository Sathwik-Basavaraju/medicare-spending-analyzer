"""Anonymise the CMS raw slice into the repo sample.

Input:  data/raw_cms_first5000.json (from src/download_cms.py, NOT committed)
Output: data/sample_providers.csv (committed, <1 MB)

Dropped for privacy / focus: NPI, provider name, credentials,
street address, city, ZIP, RUCA, and all beneficiary demographic /
condition columns. Kept: specialty (Rndrng_Prvdr_Type), state
(Rndrng_Prvdr_State_Abrvtn), total beneficiaries, total services,
total Medicare payment, total allowed amount, average beneficiary
risk score (Bene_Avg_Risk_Scre). Providers are given a sequential
anonymised ID (P00001...) in API order — this is NOT an NPI and
cannot be used to identify a provider.

Payments are converted to float; rows with missing / zero
beneficiaries are dropped (they cannot give a per-beneficiary rate).
"""

import argparse
import json
import pathlib

import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/raw_cms_first5000.json")
    ap.add_argument("--output", default="data/sample_providers.csv")
    args = ap.parse_args()
    inp = pathlib.Path(args.input)
    if inp.suffix.lower() == ".csv":
        df = pd.read_csv(inp)
    else:
        rows = json.loads(inp.read_text())
        df = pd.DataFrame(rows)
    out = pd.DataFrame({
        "provider_id": [f"P{i+1:05d}" for i in range(len(df))],
        "specialty": df["Rndrng_Prvdr_Type"],
        "state": df["Rndrng_Prvdr_State_Abrvtn"],
        "tot_benes": pd.to_numeric(df["Tot_Benes"], errors="coerce"),
        "tot_srvcs": pd.to_numeric(df["Tot_Srvcs"], errors="coerce"),
        "tot_payment": pd.to_numeric(df["Tot_Mdcr_Pymt_Amt"], errors="coerce"),
        "tot_allowed": pd.to_numeric(df["Tot_Mdcr_Alowd_Amt"], errors="coerce"),
        "avg_risk_score": pd.to_numeric(df["Bene_Avg_Risk_Scre"], errors="coerce"),
    })
    out = out.dropna(subset=["tot_benes", "tot_payment"])
    out = out[out["tot_benes"] > 0]
    out["payment_per_bene"] = out["tot_payment"] / out["tot_benes"]
    out["payment_per_service"] = out["tot_payment"] / out["tot_srvcs"].replace(0, pd.NA)
    out["risk_adjusted_payment_per_bene"] = out["payment_per_bene"] / out["avg_risk_score"].replace(0, pd.NA)
    out.to_csv(args.output, index=False)
    print(f"Wrote {len(out)} anonymised rows to {args.output}")


if __name__ == "__main__":
    main()
