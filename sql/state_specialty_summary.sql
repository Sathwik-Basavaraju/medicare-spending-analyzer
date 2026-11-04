-- State and specialty summaries (DuckDB dialect).
-- These power the "by specialty" and "by state" dashboard views
-- and the stakeholder questions in README.md.

-- Median payment per beneficiary by specialty (all specialties)
SELECT
    specialty,
    COUNT(*) AS n_providers,
    MEDIAN(payment_per_bene) AS median_payment_per_bene,
    MEDIAN(payment_per_service) AS median_payment_per_service,
    SUM(tot_payment) AS total_payment,
    SUM(tot_benes) AS total_benes
FROM providers
GROUP BY specialty
ORDER BY median_payment_per_bene DESC;

-- Median payment per beneficiary by state
SELECT
    state,
    COUNT(*) AS n_providers,
    MEDIAN(payment_per_bene) AS median_payment_per_bene,
    SUM(tot_payment) AS total_payment,
    SUM(tot_benes) AS total_benes
FROM providers
GROUP BY state
ORDER BY median_payment_per_bene DESC;

-- Specialty x state peer medians (region-adjusted view)
SELECT
    specialty,
    state,
    COUNT(*) AS n_providers,
    MEDIAN(payment_per_bene) AS median_payment_per_bene
FROM providers
GROUP BY specialty, state
HAVING COUNT(*) >= 10
ORDER BY specialty, median_payment_per_bene DESC;
