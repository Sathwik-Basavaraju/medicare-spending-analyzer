-- Peer-group benchmarking for Medicare spending (DuckDB dialect).
-- Run against data/sample_providers.csv (see src/analyze.py, which
-- executes the equivalent logic in DuckDB and writes the outputs).
--
-- Peer group: specialty (national). A provider is only benchmarked
-- if its specialty group has at least 30 providers, so medians and
-- standard deviations are not based on tiny groups.
-- Volume adjustment: payment_per_bene already divides by beneficiaries.
-- Risk adjustment: risk_adjusted_payment_per_bene divides by the
-- beneficiary average risk score, where available.
-- Region adjustment: a second peer view groups by specialty + state
-- (see sql/state_specialty_summary.sql); outliers in this file are
-- national-specialty outliers, flagged as REVIEW CANDIDATES ONLY.

-- 1. Specialty peer statistics
CREATE OR REPLACE VIEW peer_specialty AS
SELECT
    specialty,
    COUNT(*) AS n_providers,
    MEDIAN(payment_per_bene) AS peer_median_payment_per_bene,
    STDDEV(payment_per_bene) AS peer_std_payment_per_bene,
    MEDIAN(payment_per_service) AS peer_median_payment_per_service,
    MEDIAN(risk_adjusted_payment_per_bene) AS peer_median_risk_adj_payment_per_bene
FROM providers
GROUP BY specialty
HAVING COUNT(*) >= 30;

-- 2. Provider z-scores vs their specialty peer group
CREATE OR REPLACE VIEW provider_benchmark AS
SELECT
    p.provider_id,
    p.specialty,
    p.state,
    p.tot_benes,
    p.tot_srvcs,
    p.tot_payment,
    p.payment_per_bene,
    p.payment_per_service,
    p.risk_adjusted_payment_per_bene,
    peer.peer_median_payment_per_bene,
    peer.peer_std_payment_per_bene,
    (p.payment_per_bene - peer.peer_median_payment_per_bene)
        / NULLIF(peer.peer_std_payment_per_bene, 0) AS z_payment_per_bene,
    p.payment_per_bene / NULLIF(peer.peer_median_payment_per_bene, 0) AS ratio_to_peer_median
FROM providers p
JOIN peer_specialty peer USING (specialty);

-- 3. Outliers: review candidates ONLY (not findings of wrongdoing).
--    Definition used in this repo: z > 2.0 AND tot_benes >= 100.
--    The tot_benes floor avoids flagging very small panels on a noisy rate.
CREATE OR REPLACE VIEW outliers AS
SELECT *
FROM provider_benchmark
WHERE z_payment_per_bene > 2.0
  AND tot_benes >= 100
ORDER BY z_payment_per_bene DESC;
