-- ============================================================
-- GOVERNMENT PROCUREMENT INTELLIGENCE
-- CONTRACTS FINDER 2025
--
-- PROCUREMENT ANALYSIS
-- ============================================================


-- ============================================================
-- 1. OVERALL PROCUREMENT ACTIVITY
-- ============================================================

SELECT
    COUNT(*) AS total_procurements
FROM procurements;


-- ============================================================
-- 2. PROCUREMENT ACTIVITY BY CATEGORY
-- ============================================================

SELECT
    COALESCE(procurement_category, 'Unknown') AS procurement_category,
    COUNT(*) AS procurement_count,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage_of_procurements
FROM procurements
GROUP BY COALESCE(procurement_category, 'Unknown')
ORDER BY procurement_count DESC;


-- ============================================================
-- 3. PROCUREMENT ACTIVITY BY PROCUREMENT METHOD
-- ============================================================

SELECT
    COALESCE(procurement_method, 'Unknown') AS procurement_method,
    COUNT(*) AS procurement_count,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage_of_procurements
FROM procurements
GROUP BY COALESCE(procurement_method, 'Unknown')
ORDER BY procurement_count DESC;


-- ============================================================
-- 4. TENDER VALUE SUMMARY
-- ============================================================

SELECT
    COUNT(*) AS total_procurements,
    COUNT(tender_value) AS procurements_with_tender_value,
    ROUND(SUM(tender_value), 2) AS total_tender_value,
    ROUND(AVG(tender_value), 2) AS average_tender_value,
    ROUND(MIN(tender_value), 2) AS minimum_tender_value,
    ROUND(MAX(tender_value), 2) AS maximum_tender_value
FROM procurements;


-- ============================================================
-- 5. TENDER VALUE BY PROCUREMENT CATEGORY
-- ============================================================

SELECT
    COALESCE(procurement_category, 'Unknown') AS procurement_category,
    COUNT(*) AS procurement_count,
    COUNT(tender_value) AS procurements_with_value,
    ROUND(SUM(tender_value), 2) AS total_tender_value,
    ROUND(AVG(tender_value), 2) AS average_tender_value
FROM procurements
GROUP BY COALESCE(procurement_category, 'Unknown')
ORDER BY total_tender_value DESC;


-- ============================================================
-- 6. TOP BUYERS BY PROCUREMENT COUNT
-- ============================================================

SELECT
    buyer_name,
    COUNT(*) AS procurement_count
FROM procurements
WHERE buyer_name IS NOT NULL
GROUP BY buyer_name
ORDER BY procurement_count DESC
LIMIT 20;


-- ============================================================
-- 7. TOP BUYERS BY RECORDED TENDER VALUE
-- ============================================================

SELECT
    buyer_name,
    COUNT(*) AS procurement_count,
    COUNT(tender_value) AS procurements_with_value,
    ROUND(SUM(tender_value), 2) AS total_tender_value,
    ROUND(AVG(tender_value), 2) AS average_tender_value
FROM procurements
WHERE buyer_name IS NOT NULL
GROUP BY buyer_name
ORDER BY total_tender_value DESC
LIMIT 20;


-- ============================================================
-- 8. TENDER VALUE COMPLETENESS
-- ============================================================

SELECT
    COUNT(*) AS total_procurements,
    COUNT(tender_value) AS procurements_with_tender_value,
    COUNT(*) - COUNT(tender_value) AS procurements_missing_tender_value,
    ROUND(
        100.0 * COUNT(tender_value) / COUNT(*),
        2
    ) AS tender_value_completion_percentage
FROM procurements;


-- ============================================================
-- 9. PROCUREMENT METHOD BY CATEGORY
-- ============================================================

SELECT
    COALESCE(procurement_method, 'Unknown') AS procurement_method,
    COALESCE(procurement_category, 'Unknown') AS procurement_category,
    COUNT(*) AS procurement_count,
    ROUND(SUM(tender_value), 2) AS total_tender_value
FROM procurements
GROUP BY
    COALESCE(procurement_method, 'Unknown'),
    COALESCE(procurement_category, 'Unknown')
ORDER BY total_tender_value DESC;


-- ============================================================
-- 10. LARGEST INDIVIDUAL TENDER VALUES
-- ============================================================

SELECT
    tender_title,
    buyer_name,
    procurement_method,
    procurement_category,
    ROUND(tender_value, 2) AS tender_value
FROM procurements
WHERE tender_value IS NOT NULL
ORDER BY tender_value DESC
LIMIT 20;


-- ============================================================
-- 11. MEDIAN TENDER VALUE
-- ============================================================

WITH ranked AS (
    SELECT
        tender_value,
        ROW_NUMBER() OVER (
            ORDER BY tender_value
        ) AS rn,
        COUNT(*) OVER () AS n
    FROM procurements
    WHERE tender_value IS NOT NULL
)
SELECT
    ROUND(AVG(tender_value), 2) AS median_tender_value
FROM ranked
WHERE rn IN (
    (n + 1) / 2,
    (n + 2) / 2
);


-- ============================================================
-- 12. TENDER VALUE DISTRIBUTION BY VALUE BAND
-- ============================================================

WITH bands AS (
    SELECT
        CASE
            WHEN tender_value < 100000
                THEN '< £100K'

            WHEN tender_value < 1000000
                THEN '£100K - < £1M'

            WHEN tender_value < 10000000
                THEN '£1M - < £10M'

            WHEN tender_value < 100000000
                THEN '£10M - < £100M'

            WHEN tender_value < 1000000000
                THEN '£100M - < £1B'

            ELSE '£1B+'
        END AS value_band,

        tender_value

    FROM procurements
    WHERE tender_value IS NOT NULL
)

SELECT
    value_band,
    COUNT(*) AS procurement_count,

    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage_of_procurements,

    ROUND(
        SUM(tender_value),
        2
    ) AS total_tender_value,

    ROUND(
        AVG(tender_value),
        2
    ) AS average_tender_value

FROM bands

GROUP BY value_band

ORDER BY
    CASE value_band
        WHEN '< £100K' THEN 1
        WHEN '£100K - < £1M' THEN 2
        WHEN '£1M - < £10M' THEN 3
        WHEN '£10M - < £100M' THEN 4
        WHEN '£100M - < £1B' THEN 5
        WHEN '£1B+' THEN 6
    END;


-- ============================================================
-- 13. TENDER VALUE CONCENTRATION
-- ============================================================

WITH ranked AS (
    SELECT
        tender_value,

        ROW_NUMBER() OVER (
            ORDER BY tender_value DESC
        ) AS rn,

        COUNT(*) OVER () AS total_rows

    FROM procurements
    WHERE tender_value IS NOT NULL
),

total_value AS (
    SELECT
        SUM(tender_value) AS total_tender_value

    FROM procurements
    WHERE tender_value IS NOT NULL
)

SELECT
    'Top 1%' AS segment,

    COUNT(*) AS procurement_count,

    ROUND(
        SUM(tender_value),
        2
    ) AS tender_value,

    ROUND(
        100.0 * SUM(tender_value)
        / total_value.total_tender_value,
        2
    ) AS percentage_of_total_value

FROM ranked

CROSS JOIN total_value

WHERE rn <= total_rows * 0.01;


WITH ranked AS (
    SELECT
        tender_value,

        ROW_NUMBER() OVER (
            ORDER BY tender_value DESC
        ) AS rn,

        COUNT(*) OVER () AS total_rows

    FROM procurements
    WHERE tender_value IS NOT NULL
),

total_value AS (
    SELECT
        SUM(tender_value) AS total_tender_value

    FROM procurements
    WHERE tender_value IS NOT NULL
)

SELECT
    'Top 5%' AS segment,

    COUNT(*) AS procurement_count,

    ROUND(
        SUM(tender_value),
        2
    ) AS tender_value,

    ROUND(
        100.0 * SUM(tender_value)
        / total_value.total_tender_value,
        2
    ) AS percentage_of_total_value

FROM ranked

CROSS JOIN total_value

WHERE rn <= total_rows * 0.05;


WITH ranked AS (
    SELECT
        tender_value,

        ROW_NUMBER() OVER (
            ORDER BY tender_value DESC
        ) AS rn,

        COUNT(*) OVER () AS total_rows

    FROM procurements
    WHERE tender_value IS NOT NULL
),

total_value AS (
    SELECT
        SUM(tender_value) AS total_tender_value

    FROM procurements
    WHERE tender_value IS NOT NULL
)

SELECT
    'Top 10%' AS segment,

    COUNT(*) AS procurement_count,

    ROUND(
        SUM(tender_value),
        2
    ) AS tender_value,

    ROUND(
        100.0 * SUM(tender_value)
        / total_value.total_tender_value,
        2
    ) AS percentage_of_total_value

FROM ranked

CROSS JOIN total_value

WHERE rn <= total_rows * 0.10;


-- ============================================================
-- 14. LARGE TENDER VALUE THRESHOLDS
-- ============================================================

WITH thresholds AS (

    SELECT
        '£1B+' AS threshold,
        1000000000 AS minimum_value

    UNION ALL

    SELECT
        '£5B+',
        5000000000

    UNION ALL

    SELECT
        '£10B+',
        10000000000

    UNION ALL

    SELECT
        '£50B+',
        50000000000
),

totals AS (

    SELECT
        COUNT(*) AS total_procurements,
        SUM(tender_value) AS total_tender_value

    FROM procurements

    WHERE tender_value IS NOT NULL
)

SELECT
    thresholds.threshold,

    COUNT(p.ocid) AS procurement_count,

    ROUND(
        COALESCE(SUM(p.tender_value), 0),
        2
    ) AS tender_value,

    ROUND(
        100.0
        * COUNT(p.ocid)
        / totals.total_procurements,
        2
    ) AS percentage_of_procurements,

    ROUND(
        100.0
        * COALESCE(SUM(p.tender_value), 0)
        / totals.total_tender_value,
        2
    ) AS percentage_of_total_value

FROM thresholds

CROSS JOIN totals

LEFT JOIN procurements AS p
    ON p.tender_value >= thresholds.minimum_value

GROUP BY
    thresholds.threshold,
    thresholds.minimum_value,
    totals.total_procurements,
    totals.total_tender_value

ORDER BY
    thresholds.minimum_value;


-- ============================================================
-- 15. TOP BUYERS BY RECORDED TENDER VALUE CONCENTRATION
-- ============================================================

WITH buyer_totals AS (

    SELECT
        buyer_name,
        COUNT(*) AS procurement_count,
        SUM(tender_value) AS buyer_tender_value

    FROM procurements

    WHERE tender_value IS NOT NULL
      AND buyer_name IS NOT NULL

    GROUP BY buyer_name
),

grand_total AS (

    SELECT
        SUM(tender_value) AS total_tender_value

    FROM procurements

    WHERE tender_value IS NOT NULL
)

SELECT
    buyer_totals.buyer_name,

    buyer_totals.procurement_count,

    ROUND(
        buyer_totals.buyer_tender_value,
        2
    ) AS total_tender_value,

    ROUND(
        100.0
        * buyer_totals.buyer_tender_value
        / grand_total.total_tender_value,
        2
    ) AS percentage_of_total_value

FROM buyer_totals

CROSS JOIN grand_total

ORDER BY buyer_totals.buyer_tender_value DESC

LIMIT 20;

-- ============================================================
-- 16. EXTREME TENDER VALUE INVESTIGATION
-- ============================================================

-- Identify all procurements with tender values of £10B or more.

SELECT
    ocid,
    tender_title,
    buyer_name,
    procurement_method,
    procurement_category,
    tender_value,
    tender_currency
FROM procurements
WHERE tender_value >= 10000000000
ORDER BY tender_value DESC;


-- ============================================================
-- 17. EXTREME TENDER VALUES BY BUYER
-- ============================================================

SELECT
    buyer_name,
    COUNT(*) AS extreme_tender_count,
    ROUND(SUM(tender_value), 2) AS total_extreme_tender_value,
    ROUND(AVG(tender_value), 2) AS average_extreme_tender_value,
    ROUND(MAX(tender_value), 2) AS maximum_tender_value
FROM procurements
WHERE tender_value >= 10000000000
GROUP BY buyer_name
ORDER BY total_extreme_tender_value DESC;


-- ============================================================
-- 18. EXTREME TENDER VALUES BY CATEGORY
-- ============================================================

SELECT
    COALESCE(procurement_category, 'Unknown') AS procurement_category,
    COUNT(*) AS extreme_tender_count,
    ROUND(SUM(tender_value), 2) AS total_extreme_tender_value,
    ROUND(AVG(tender_value), 2) AS average_extreme_tender_value
FROM procurements
WHERE tender_value >= 10000000000
GROUP BY COALESCE(procurement_category, 'Unknown')
ORDER BY total_extreme_tender_value DESC;


-- ============================================================
-- 19. EXTREME TENDER VALUES BY PROCUREMENT METHOD
-- ============================================================

SELECT
    COALESCE(procurement_method, 'Unknown') AS procurement_method,
    COUNT(*) AS extreme_tender_count,
    ROUND(SUM(tender_value), 2) AS total_extreme_tender_value,
    ROUND(AVG(tender_value), 2) AS average_extreme_tender_value
FROM procurements
WHERE tender_value >= 10000000000
GROUP BY COALESCE(procurement_method, 'Unknown')
ORDER BY total_extreme_tender_value DESC;


-- ============================================================
-- 20. TENDER VALUE DISTRIBUTION AFTER REMOVING EXTREME VALUES
-- ============================================================

SELECT
    COUNT(*) AS procurements_under_10bn,
    COUNT(tender_value) AS valued_procurements_under_10bn,
    ROUND(SUM(tender_value), 2) AS total_tender_value_under_10bn,
    ROUND(AVG(tender_value), 2) AS average_tender_value_under_10bn,
    ROUND(MIN(tender_value), 2) AS minimum_tender_value_under_10bn,
    ROUND(MAX(tender_value), 2) AS maximum_tender_value_under_10bn
FROM procurements
WHERE tender_value IS NOT NULL
  AND tender_value < 10000000000;


-- ============================================================
-- 21. TOP EXTREME TENDERS WITH PROCUREMENT IDENTIFIERS
-- ============================================================

SELECT
    ocid,
    tender_title,
    buyer_name,
    procurement_method,
    procurement_category,
    ROUND(tender_value, 2) AS tender_value
FROM procurements
WHERE tender_value >= 10000000000
ORDER BY tender_value DESC
LIMIT 20;