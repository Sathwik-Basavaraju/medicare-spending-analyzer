# Data Sources — Medicare Spending Variation

## Primary source (used, no substitution)
- **CMS Medicare Physician & Other Practitioners – by Provider**,
  via the data.cms.gov Provider Data API.
- API dataset UUID: `44ea2789-993f-4d55-ac44-ed7f160b58fa`
- Endpoint: `https://data.cms.gov/data-api/v1/dataset/{uuid}/data`
- Slice fetched 2026-11-04: first 5,000 rows in API default order
  (size=1000, offset 0, 1000, 2000, 3000, 4000), no filter, no sort.
  Fetch script: `src/download_cms.py`.

## Sample shipped in this repo
- `data/sample_providers.csv`: 5,000 anonymised rows, built by
  `src/build_sample.py` from the raw API slice.
- Dropped: NPI, provider name, credentials, street address, city,
  ZIP, RUCA, and all beneficiary demographic / condition columns.
- Kept: specialty, state, total beneficiaries, total services,
  total Medicare payment, total allowed amount, average risk score,
  plus derived payment-per-beneficiary / per-service /
  risk-adjusted rates. Provider IDs are sequential (`P00001…`)
  in API order and are NOT NPIs.

## No substitution was needed
The CMS API worked for the documented slice. The full CMS dataset
is much larger; this repo deliberately uses only the 5,000-row
slice above, and all metrics in `outputs/metrics.json` are for
that slice only.
