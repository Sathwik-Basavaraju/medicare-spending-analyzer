# Medicare Spending Variation Analyzer

Peer-group benchmarking of Medicare provider payments, with
statistical outliers flagged **for review only**.

> **Disclaimer — read first:** Outliers in this repo are **review
> candidates only, not findings of wrongdoing**. Payment differences
> can reflect case mix, service mix, geography, patient risk, and
> coding, which a peer-median method only partly adjusts for.
> Do not use this repo to accuse any provider of improper billing.

## What was actually computed (this run)

All numbers below are from `outputs/metrics.json`, computed by
`src/analyze.py` on the sample in `data/sample_providers.csv`:

- Providers in sample: **5,000**
- Providers benchmarked (specialty groups with n ≥ 30): **4,541**
- Specialties in sample: **82**
- States / territories in sample: **55**
- Outliers (z > 2.0 vs specialty peer median/std, tot_benes ≥ 100): **119**
- Outliers as share of benchmarked providers: **2.62%**
- Median Medicare payment per beneficiary (all sample): **$157.82**
- Median Medicare payment per service (all sample): **$56.21**
- Total Medicare payment in sample: **$363,873,147**
- Total beneficiaries in sample: **1,452,395**
- Top outlier specialties by count: Nurse Practitioner (27),
  Family Practice (9), Certified Registered Nurse Anesthetist (9),
  Anesthesiology (8), Internal Medicine (7) — full breakdown in
  `outputs/metrics.json` (`outliers_by_specialty`).
- Top outlier states by count: CA (19), TX (14), FL (10), NY (8) —
  full breakdown in `outputs/metrics.json` (`outliers_by_state`).

No placeholder numbers are used in this README. If you re-run the
analysis on a different slice, re-read `outputs/metrics.json` —
these numbers will change.

## Data source (exact slice)

- **Source:** CMS Medicare Physician & Other Practitioners – by
  Provider, via the data.cms.gov Provider Data API.
- **API dataset UUID:** `44ea2789-993f-4d55-ac44-ed7f160b58fa`
- **Slice used:** the **first 5,000 rows returned by the API in its
  default order** (no filter, no sort), fetched 2026-11-04 with
  `src/download_cms.py` (size=1000, offset 0–4000).
- **Anonymisation:** the raw API rows contain provider names, NPIs
  and addresses. Those fields were **dropped** by
  `src/build_sample.py`. The repo sample keeps only specialty,
  state, beneficiary/service/payment totals, and average risk score,
  with a sequential anonymised ID (`P00001…`) in API order.
  That ID is **not** an NPI and cannot identify a provider.
- **No substitution was needed:** the CMS API worked for this slice.
  The full CMS dataset is much larger; this repo deliberately uses
  only the documented 5,000-row slice above.

## Method

1. **Per-provider rates** (in `src/build_sample.py`):
   payment_per_bene = tot_payment / tot_benes;
   payment_per_service = tot_payment / tot_srvcs;
   risk_adjusted_payment_per_bene = payment_per_bene / avg_risk_score.
2. **Peer groups** (`sql/peer_benchmark.sql`, executed in DuckDB
   by `src/analyze.py`): specialty, national, minimum 30 providers
   per group. Peer median and standard deviation of
   payment_per_bene are computed per specialty.
3. **Volume adjustment:** dividing by beneficiaries already
   normalises for panel size. A tot_benes ≥ 100 floor is also
   applied to outliers, to avoid flagging very small panels on a
   noisy rate.
4. **Region adjustment (documented, partial):** a second view
   groups by specialty + state (`sql/state_specialty_summary.sql`).
   Outliers in `outputs/outliers.csv` are national-specialty
   outliers; state is reported for each outlier so a reviewer can
   check the state peer view too. Risk adjustment is shown as a
   separate column, not folded into the headline z-score, so the
   headline definition stays auditable.
5. **Outlier rule:** z = (payment_per_bene − peer_median) / peer_std
   > 2.0, and tot_benes ≥ 100.
6. **Limitations:** peer medians do not fully adjust for case mix,
   service mix, or patient complexity; a high z-score can be
   legitimate (e.g. a procedure-heavy specialty mix within a broad
   specialty label). Treat every outlier as a prompt for review,
   not a conclusion.

## Stakeholder questions answered

1. **Which specialties have the highest median payment per
   beneficiary?** — `outputs/specialty_summary.csv`,
   `outputs/charts/median_by_specialty.png`, dashboard § Specialty.
2. **Which states have the highest median payment per beneficiary?**
   — `outputs/state_summary.csv`,
   `outputs/charts/median_by_state.png`, dashboard § State.
3. **How is payment per beneficiary distributed?** —
   `outputs/charts/payment_per_bene_distribution.png`.
4. **Which providers are statistical outliers, and by how much?**
   — `outputs/outliers.csv` (provider_id, specialty, state,
   payment_per_bene, peer_median, z, ratio_to_median),
   `outputs/charts/outlier_scatter.png`.
5. **Do outliers concentrate in particular specialties or states?**
   — `outputs/metrics.json`: `outliers_by_specialty`,
   `outliers_by_state`.
6. **What is a provider's payment per service, not just per
   beneficiary?** — `payment_per_service` column in the sample
   and benchmark files; specialty medians in
   `outputs/specialty_summary.csv`.
7. **How does risk adjustment change the picture?** —
   `risk_adjusted_payment_per_bene` column; compare it with
   `payment_per_bene` for the same provider in
   `outputs/provider_benchmark.csv`.
8. **How do I rebuild this in Tableau?** — `tableau_notes.md`
   (sheets, filters, calculated fields, including the outlier flag).

## Files

- `src/download_cms.py` — fetch the documented CMS slice (raw file
  is NOT committed).
- `src/build_sample.py` — anonymise raw CMS rows to the repo sample.
- `src/analyze.py` — DuckDB benchmarking, metrics, outliers, charts.
- `sql/peer_benchmark.sql`, `sql/state_specialty_summary.sql` — SQL
  used (DuckDB dialect).
- `data/sample_providers.csv` — anonymised sample (5,000 rows).
- `outputs/metrics.json`, `outputs/outliers.csv`,
  `outputs/provider_benchmark.csv`, `outputs/specialty_summary.csv`,
  `outputs/state_summary.csv`, `outputs/charts/*.png`.
- `dashboard/app.py` — Streamlit dashboard (demo over the sample).
- `tableau_notes.md` — Tableau rebuild guide (no .twbx included).

## How to run

```bash
python3 -m venv .venv && .venv/bin/activate
pip install -r requirements.txt
# To reproduce the sample from the API (raw file not committed):
python3 src/download_cms.py --n 5000 --out data/raw_cms_first5000.json
python3 src/build_sample.py --input data/raw_cms_first5000.json \
    --output data/sample_providers.csv
# Or, using the shipped sample directly:
python3 src/analyze.py --input data/sample_providers.csv
streamlit run dashboard/app.py
```

## Requirements

See `requirements.txt` (pandas, duckdb, matplotlib, streamlit).
System Python in this build environment lacked scikit-learn /
DuckDB, so a workspace venv was used for testing; see
`requirements.txt` for the versions to install in a fresh venv.
