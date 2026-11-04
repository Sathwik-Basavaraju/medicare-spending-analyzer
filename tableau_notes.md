# Tableau Rebuild Guide — Medicare Spending Variation

**No .twbx file is included in this repo.** Use the steps below to
rebuild the dashboard in Tableau Desktop / Public from
`data/sample_providers.csv` (anonymised) and `outputs/outliers.csv`.

## Data sources
- `data/sample_providers.csv`: provider_id (anonymised), specialty,
  state, tot_benes, tot_srvcs, tot_payment, tot_allowed,
  avg_risk_score, payment_per_bene, payment_per_service,
  risk_adjusted_payment_per_bene.
- `outputs/outliers.csv`: provider benchmark + z-score + ratio.

## Calculated fields
- `Payment per Bene` = `[tot_payment] / [tot_benes]`
  (already a column in the sample; use the column or this calc.)
- `Payment per Service` = `[tot_payment] / [tot_srvcs]`
- `Peer Median (specialty)` = `{FIXED [specialty] : MEDIAN([payment_per_bene])}`
- `Z vs Specialty Peer` = `([payment_per_bene] - [Peer Median (specialty)]) / {FIXED [specialty] : STDEV([payment_per_bene])}`
  (use the precomputed `z` column in outliers.csv to cross-check.)
- `Outlier Flag (review candidate)` =
  `IF [Z vs Specialty Peer] > 2 AND [tot_benes] >= 100 THEN "Review candidate" ELSE "Not flagged" END`

## Sheets to build
1. **Specialty median payment** — bar, specialty vs median payment
   per beneficiary, sorted descending, filter: specialty.
2. **State variation** — bar, state vs median payment per beneficiary.
3. **Outlier scatter** — tot_benes (log axis) vs payment per
   beneficiary, colour by Outlier Flag; tooltip: specialty, state,
   peer median, z-score.
4. **Outlier table** — anonymised provider_id, specialty, state,
   beneficiaries, payment per bene, peer median, z-score, sorted
   by z descending. Title it "Review candidates only".

## Dashboard assembly + filters
- One dashboard with the four sheets, filters: specialty, state.
- Add a text box with the disclaimer: "Outliers are review
  candidates only, not findings of wrongdoing. Differences can
  reflect case mix, service mix, geography and risk."

## Stakeholder questions (and where each is answered)
See README.md, "Stakeholder questions answered" — each question
maps to a sheet, SQL file, or metrics.json field above.
