-- ============================================================================
-- CONTRACTS FINDER 2025
-- SUPPLIER INTELLIGENCE & SUPPLIER CONCENTRATION ANALYSIS
-- ============================================================================
--
-- Purpose:
-- Analyse supplier participation, supplier identity quality, buyer-supplier
-- relationships, supplier diversification, multi-supplier awards and
-- supplier-level award-value concentration.
--
-- IMPORTANT METHODOLOGY NOTE
-- --------------------------
-- Where an award involved multiple suppliers, the recorded award value is
-- allocated equally across the associated suppliers for supplier-level
-- concentration analysis.
--
-- This prevents the same award value from being counted multiple times.
-- The allocation is an analytical assumption and must NOT be interpreted as
-- actual supplier payment, expenditure or revenue.
--
-- Supplier names identified as missing, redacted, or source-text contamination
-- are excluded from supplier-value ranking/concentration analysis where
-- appropriate.
-- ============================================================================


-- ============================================================================
-- QUERY 1
-- OVERALL SUPPLIER ACTIVITY
-- ============================================================================

SELECT
    COUNT(DISTINCT supplier_key) AS unique_suppliers,
    COUNT(*) AS supplier_relationships,
    COUNT(DISTINCT award_id) AS awards_with_suppliers
FROM award_suppliers;


-- ============================================================================
-- QUERY 2
-- SUPPLIER IDENTITY REVIEW
-- ============================================================================

SELECT
    identity_review_flag,
    COUNT(*) AS supplier_count
FROM suppliers
GROUP BY identity_review_flag
ORDER BY supplier_count DESC;


-- ============================================================================
-- QUERY 3
-- SUPPLIER ID QUALITY
-- ============================================================================

SELECT
    supplier_id_quality,
    COUNT(*) AS supplier_count
FROM suppliers
GROUP BY supplier_id_quality
ORDER BY supplier_count DESC;


-- ============================================================================
-- QUERY 4
-- SUPPLIER NAME QUALITY
-- ============================================================================

WITH supplier_quality AS (
    SELECT
        supplier_key,
        canonical_supplier_name,
        CASE
            WHEN canonical_supplier_name IS NULL
                OR TRIM(canonical_supplier_name) = ''
                THEN 'Missing supplier name'

            WHEN LOWER(canonical_supplier_name) LIKE '%redacted%'
                OR LOWER(canonical_supplier_name) LIKE '%foia%'
                THEN 'Redacted / unavailable'

            WHEN LOWER(canonical_supplier_name) LIKE '%successful supplier%'
                OR LOWER(canonical_supplier_name) LIKE '%supplier list%'
                OR LOWER(canonical_supplier_name) LIKE '%see contracts finder%'
                OR LOWER(canonical_supplier_name) LIKE '%see webpage%'
                OR LOWER(canonical_supplier_name) LIKE '%contract award details%'
                OR LOWER(canonical_supplier_name) LIKE '%attachments%'
                THEN 'Source-text contamination'

            ELSE 'Usable supplier name'
        END AS supplier_name_quality
    FROM suppliers
)

SELECT
    supplier_name_quality,
    COUNT(*) AS supplier_count
FROM supplier_quality
GROUP BY supplier_name_quality
ORDER BY supplier_count DESC;


-- ============================================================================
-- QUERY 5
-- LATEST AWARD POPULATION
-- ============================================================================

SELECT
    COUNT(*) AS latest_award_versions,
    COUNT(DISTINCT award_id) AS unique_awards,
    SUM(
        CASE
            WHEN award_value IS NOT NULL THEN 1
            ELSE 0
        END
    ) AS awards_with_value,
    SUM(
        CASE
            WHEN award_value IS NULL THEN 1
            ELSE 0
        END
    ) AS awards_missing_value,
    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN award_value IS NOT NULL THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS value_completeness_pct
FROM award_versions
WHERE is_latest_award_version = 1
  AND award_id IN (
      SELECT DISTINCT award_id
      FROM award_suppliers
  );


-- ============================================================================
-- QUERY 6
-- TOP SUPPLIERS BY AWARD COUNT
-- ============================================================================

SELECT
    s.supplier_key,
    s.canonical_supplier_name,
    COUNT(DISTINCT a.award_id) AS award_count,
    COUNT(DISTINCT a.ocid) AS procurement_count,
    COUNT(DISTINCT p.buyer_name) AS buyer_count
FROM suppliers s
JOIN award_suppliers a
    ON s.supplier_key = a.supplier_key
JOIN procurements p
    ON a.ocid = p.ocid
WHERE s.canonical_supplier_name IS NOT NULL
GROUP BY
    s.supplier_key,
    s.canonical_supplier_name
ORDER BY award_count DESC
LIMIT 25;


-- ============================================================================
-- QUERY 7
-- TOP SUPPLIERS BY ALLOCATED AWARD VALUE
-- ============================================================================

WITH supplier_name_quality AS (
    SELECT
        supplier_key,
        canonical_supplier_name,
        CASE
            WHEN canonical_supplier_name IS NULL
                OR TRIM(canonical_supplier_name) = ''
                THEN 'Missing supplier name'

            WHEN LOWER(canonical_supplier_name) LIKE '%redacted%'
                OR LOWER(canonical_supplier_name) LIKE '%foia%'
                THEN 'Redacted / unavailable'

            WHEN LOWER(canonical_supplier_name) LIKE '%successful supplier%'
                OR LOWER(canonical_supplier_name) LIKE '%supplier list%'
                OR LOWER(canonical_supplier_name) LIKE '%see contracts finder%'
                OR LOWER(canonical_supplier_name) LIKE '%see webpage%'
                OR LOWER(canonical_supplier_name) LIKE '%contract award details%'
                OR LOWER(canonical_supplier_name) LIKE '%attachments%'
                THEN 'Source-text contamination'

            ELSE 'Usable supplier name'
        END AS supplier_name_quality
    FROM suppliers
),

supplier_counts AS (
    SELECT
        award_id,
        COUNT(DISTINCT supplier_key) AS supplier_count
    FROM award_suppliers
    GROUP BY award_id
),

latest_awards AS (
    SELECT
        award_id,
        award_value
    FROM award_versions
    WHERE is_latest_award_version = 1
),

allocated_values AS (
    SELECT
        a.supplier_key,
        SUM(
            CASE
                WHEN aw.award_value IS NOT NULL
                THEN aw.award_value / NULLIF(sc.supplier_count, 0)
                ELSE 0
            END
        ) AS allocated_award_value,
        COUNT(DISTINCT a.award_id) AS award_count
    FROM award_suppliers a
    JOIN supplier_counts sc
        ON a.award_id = sc.award_id
    JOIN latest_awards aw
        ON a.award_id = aw.award_id
    GROUP BY a.supplier_key
)

SELECT
    av.supplier_key,
    sq.canonical_supplier_name,
    av.award_count,
    ROUND(av.allocated_award_value, 2) AS allocated_award_value
FROM allocated_values av
JOIN supplier_name_quality sq
    ON av.supplier_key = sq.supplier_key
WHERE sq.supplier_name_quality = 'Usable supplier name'
ORDER BY av.allocated_award_value DESC
LIMIT 25;


-- ============================================================================
-- QUERY 8
-- TOP BUYER-SUPPLIER RELATIONSHIPS BY AWARD COUNT
-- ============================================================================

SELECT
    p.buyer_name,
    s.canonical_supplier_name,
    COUNT(DISTINCT a.award_id) AS award_count,
    COUNT(DISTINCT a.supplier_key) AS supplier_key_count
FROM award_suppliers a
JOIN suppliers s
    ON a.supplier_key = s.supplier_key
JOIN procurements p
    ON a.ocid = p.ocid
WHERE s.canonical_supplier_name IS NOT NULL
GROUP BY
    p.buyer_name,
    s.canonical_supplier_name
ORDER BY award_count DESC
LIMIT 25;


-- ============================================================================
-- QUERY 9
-- SUPPLIERS SERVING MULTIPLE BUYERS
-- ============================================================================

WITH supplier_name_quality AS (
    SELECT
        supplier_key,
        canonical_supplier_name,
        CASE
            WHEN canonical_supplier_name IS NULL
                OR TRIM(canonical_supplier_name) = ''
                THEN 'Missing supplier name'

            WHEN LOWER(canonical_supplier_name) LIKE '%redacted%'
                OR LOWER(canonical_supplier_name) LIKE '%foia%'
                THEN 'Redacted / unavailable'

            WHEN LOWER(canonical_supplier_name) LIKE '%successful supplier%'
                OR LOWER(canonical_supplier_name) LIKE '%supplier list%'
                OR LOWER(canonical_supplier_name) LIKE '%see contracts finder%'
                OR LOWER(canonical_supplier_name) LIKE '%see webpage%'
                OR LOWER(canonical_supplier_name) LIKE '%contract award details%'
                OR LOWER(canonical_supplier_name) LIKE '%attachments%'
                THEN 'Source-text contamination'

            ELSE 'Usable supplier name'
        END AS supplier_name_quality
    FROM suppliers
),

supplier_counts AS (
    SELECT
        award_id,
        COUNT(DISTINCT supplier_key) AS supplier_count
    FROM award_suppliers
    GROUP BY award_id
),

latest_awards AS (
    SELECT
        award_id,
        award_value
    FROM award_versions
    WHERE is_latest_award_version = 1
),

supplier_values AS (
    SELECT
        a.supplier_key,
        SUM(
            CASE
                WHEN aw.award_value IS NOT NULL
                THEN aw.award_value / NULLIF(sc.supplier_count, 0)
                ELSE 0
            END
        ) AS allocated_award_value
    FROM award_suppliers a
    JOIN supplier_counts sc
        ON a.award_id = sc.award_id
    JOIN latest_awards aw
        ON a.award_id = aw.award_id
    GROUP BY a.supplier_key
)

SELECT
    s.supplier_key,
    s.canonical_supplier_name,
    COUNT(DISTINCT p.buyer_name) AS buyer_count,
    COUNT(DISTINCT a.award_id) AS award_count,
    ROUND(COALESCE(sv.allocated_award_value, 0), 2)
        AS allocated_award_value
FROM suppliers s
JOIN award_suppliers a
    ON s.supplier_key = a.supplier_key
JOIN procurements p
    ON a.ocid = p.ocid
LEFT JOIN supplier_values sv
    ON s.supplier_key = sv.supplier_key
JOIN supplier_name_quality sq
    ON s.supplier_key = sq.supplier_key
WHERE sq.supplier_name_quality = 'Usable supplier name'
GROUP BY
    s.supplier_key,
    s.canonical_supplier_name
HAVING COUNT(DISTINCT p.buyer_name) > 1
ORDER BY buyer_count DESC, award_count DESC
LIMIT 25;


-- ============================================================================
-- QUERY 10
-- MULTI-SUPPLIER AWARD STRUCTURE
-- ============================================================================

WITH supplier_counts AS (
    SELECT
        award_id,
        COUNT(DISTINCT supplier_key) AS supplier_count
    FROM award_suppliers
    GROUP BY award_id
)

SELECT
    CASE
        WHEN supplier_count = 1 THEN 'Single supplier'
        WHEN supplier_count = 2 THEN '2 suppliers'
        WHEN supplier_count = 3 THEN '3 suppliers'
        WHEN supplier_count BETWEEN 4 AND 5 THEN '4-5 suppliers'
        WHEN supplier_count BETWEEN 6 AND 10 THEN '6-10 suppliers'
        ELSE '11+ suppliers'
    END AS supplier_structure,
    COUNT(*) AS award_count
FROM supplier_counts
GROUP BY
    CASE
        WHEN supplier_count = 1 THEN 'Single supplier'
        WHEN supplier_count = 2 THEN '2 suppliers'
        WHEN supplier_count = 3 THEN '3 suppliers'
        WHEN supplier_count BETWEEN 4 AND 5 THEN '4-5 suppliers'
        WHEN supplier_count BETWEEN 6 AND 10 THEN '6-10 suppliers'
        ELSE '11+ suppliers'
    END
ORDER BY
    CASE
        WHEN supplier_structure = 'Single supplier' THEN 1
        WHEN supplier_structure = '2 suppliers' THEN 2
        WHEN supplier_structure = '3 suppliers' THEN 3
        WHEN supplier_structure = '4-5 suppliers' THEN 4
        WHEN supplier_structure = '6-10 suppliers' THEN 5
        ELSE 6
    END;


-- ============================================================================
-- QUERY 11
-- AWARD VALUE BY SUPPLIER STRUCTURE
-- ============================================================================

WITH supplier_counts AS (
    SELECT
        award_id,
        COUNT(DISTINCT supplier_key) AS supplier_count
    FROM award_suppliers
    GROUP BY award_id
),

latest_awards AS (
    SELECT
        award_id,
        award_value
    FROM award_versions
    WHERE is_latest_award_version = 1
),

award_structure AS (
    SELECT
        sc.award_id,
        sc.supplier_count,
        aw.award_value
    FROM supplier_counts sc
    JOIN latest_awards aw
        ON sc.award_id = aw.award_id
    WHERE aw.award_value IS NOT NULL
)

SELECT
    CASE
        WHEN supplier_count = 1 THEN 'Single supplier'
        ELSE 'Multiple suppliers'
    END AS supplier_structure,
    COUNT(*) AS award_count,
    ROUND(SUM(award_value), 2) AS recorded_award_value
FROM award_structure
GROUP BY
    CASE
        WHEN supplier_count = 1 THEN 'Single supplier'
        ELSE 'Multiple suppliers'
    END
ORDER BY recorded_award_value DESC;


-- ============================================================================
-- QUERY 12
-- SUPPLIER IDENTITY REVIEW POPULATION
-- ============================================================================

SELECT
    supplier_key,
    supplier_id,
    canonical_supplier_name,
    reported_name_count,
    relationship_count,
    supplier_id_quality,
    identity_review_flag
FROM suppliers
WHERE identity_review_flag = 'review_name_variation'
ORDER BY relationship_count DESC
LIMIT 100;


-- ============================================================================
-- QUERY 13
-- BUYER-SUPPLIER DEPENDENCY SCREENING
-- ============================================================================

WITH buyer_supplier AS (
    SELECT
        p.buyer_name,
        s.canonical_supplier_name,
        COUNT(DISTINCT a.award_id) AS supplier_awards
    FROM award_suppliers a
    JOIN suppliers s
        ON a.supplier_key = s.supplier_key
    JOIN procurements p
        ON a.ocid = p.ocid
    WHERE s.canonical_supplier_name IS NOT NULL
    GROUP BY
        p.buyer_name,
        s.canonical_supplier_name
),

buyer_totals AS (
    SELECT
        buyer_name,
        SUM(supplier_awards) AS total_awards
    FROM buyer_supplier
    GROUP BY buyer_name
)

SELECT
    bs.buyer_name,
    bs.canonical_supplier_name,
    bs.supplier_awards,
    bt.total_awards,
    ROUND(
        100.0 * bs.supplier_awards / NULLIF(bt.total_awards, 0),
        2
    ) AS top_supplier_award_share_pct
FROM buyer_supplier bs
JOIN buyer_totals bt
    ON bs.buyer_name = bt.buyer_name
WHERE bt.total_awards >= 5
ORDER BY top_supplier_award_share_pct DESC
LIMIT 25;


-- ============================================================================
-- QUERY 14
-- SUPPLIER DIVERSIFICATION
-- ============================================================================

SELECT
    s.supplier_key,
    s.canonical_supplier_name,
    COUNT(DISTINCT p.buyer_name) AS buyer_count,
    COUNT(DISTINCT a.award_id) AS award_count
FROM suppliers s
JOIN award_suppliers a
    ON s.supplier_key = a.supplier_key
JOIN procurements p
    ON a.ocid = p.ocid
WHERE s.canonical_supplier_name IS NOT NULL
GROUP BY
    s.supplier_key,
    s.canonical_supplier_name
HAVING COUNT(DISTINCT p.buyer_name) > 1
ORDER BY buyer_count DESC, award_count DESC
LIMIT 25;


-- ============================================================================
-- QUERY 15
-- SUPPLIER ALLOCATED-VALUE DISTRIBUTION
-- ============================================================================

WITH supplier_counts AS (
    SELECT
        award_id,
        COUNT(DISTINCT supplier_key) AS supplier_count
    FROM award_suppliers
    GROUP BY award_id
),

latest_awards AS (
    SELECT
        award_id,
        award_value
    FROM award_versions
    WHERE is_latest_award_version = 1
),

supplier_name_quality AS (
    SELECT
        supplier_key,
        canonical_supplier_name,
        CASE
            WHEN canonical_supplier_name IS NULL
                OR TRIM(canonical_supplier_name) = ''
                THEN 'Missing supplier name'

            WHEN LOWER(canonical_supplier_name) LIKE '%redacted%'
                OR LOWER(canonical_supplier_name) LIKE '%foia%'
                THEN 'Redacted / unavailable'

            WHEN LOWER(canonical_supplier_name) LIKE '%successful supplier%'
                OR LOWER(canonical_supplier_name) LIKE '%supplier list%'
                OR LOWER(canonical_supplier_name) LIKE '%see contracts finder%'
                OR LOWER(canonical_supplier_name) LIKE '%see webpage%'
                OR LOWER(canonical_supplier_name) LIKE '%contract award details%'
                OR LOWER(canonical_supplier_name) LIKE '%attachments%'
                THEN 'Source-text contamination'

            ELSE 'Usable supplier name'
        END AS supplier_name_quality
    FROM suppliers
),

supplier_allocations AS (
    SELECT
        a.supplier_key,
        SUM(
            CASE
                WHEN aw.award_value IS NOT NULL
                THEN aw.award_value / NULLIF(sc.supplier_count, 0)
                ELSE 0
            END
        ) AS allocated_award_value
    FROM award_suppliers a
    JOIN supplier_counts sc
        ON a.award_id = sc.award_id
    JOIN latest_awards aw
        ON a.award_id = aw.award_id
    GROUP BY a.supplier_key
)

SELECT
    CASE
        WHEN allocated_award_value < 100000
            THEN '< 100K'
        WHEN allocated_award_value < 1000000
            THEN '100K-< 1M'
        WHEN allocated_award_value < 10000000
            THEN '1M-< 10M'
        WHEN allocated_award_value < 100000000
            THEN '10M-< 100M'
        WHEN allocated_award_value < 1000000000
            THEN '100M-< 1B'
        ELSE '1B+'
    END AS supplier_value_band,
    COUNT(*) AS supplier_count,
    ROUND(SUM(allocated_award_value), 2) AS allocated_award_value
FROM supplier_allocations sa
JOIN supplier_name_quality sq
    ON sa.supplier_key = sq.supplier_key
WHERE sq.supplier_name_quality = 'Usable supplier name'
GROUP BY
    CASE
        WHEN allocated_award_value < 100000
            THEN '< 100K'
        WHEN allocated_award_value < 1000000
            THEN '100K-< 1M'
        WHEN allocated_award_value < 10000000
            THEN '1M-< 10M'
        WHEN allocated_award_value < 100000000
            THEN '10M-< 100M'
        WHEN allocated_award_value < 1000000000
            THEN '100M-< 1B'
        ELSE '1B+'
    END
ORDER BY
    CASE
        WHEN supplier_value_band = '< 100K' THEN 1
        WHEN supplier_value_band = '100K-< 1M' THEN 2
        WHEN supplier_value_band = '1M-< 10M' THEN 3
        WHEN supplier_value_band = '10M-< 100M' THEN 4
        WHEN supplier_value_band = '100M-< 1B' THEN 5
        ELSE 6
    END;


-- ============================================================================
-- QUERY 16
-- CUMULATIVE SUPPLIER VALUE CONCENTRATION
-- ============================================================================

WITH supplier_counts AS (
    SELECT
        award_id,
        COUNT(DISTINCT supplier_key) AS supplier_count
    FROM award_suppliers
    GROUP BY award_id
),

latest_awards AS (
    SELECT
        award_id,
        award_value
    FROM award_versions
    WHERE is_latest_award_version = 1
),

supplier_name_quality AS (
    SELECT
        supplier_key,
        canonical_supplier_name,
        CASE
            WHEN canonical_supplier_name IS NULL
                OR TRIM(canonical_supplier_name) = ''
                THEN 'Missing supplier name'

            WHEN LOWER(canonical_supplier_name) LIKE '%redacted%'
                OR LOWER(canonical_supplier_name) LIKE '%foia%'
                THEN 'Redacted / unavailable'

            WHEN LOWER(canonical_supplier_name) LIKE '%successful supplier%'
                OR LOWER(canonical_supplier_name) LIKE '%supplier list%'
                OR LOWER(canonical_supplier_name) LIKE '%see contracts finder%'
                OR LOWER(canonical_supplier_name) LIKE '%see webpage%'
                OR LOWER(canonical_supplier_name) LIKE '%contract award details%'
                OR LOWER(canonical_supplier_name) LIKE '%attachments%'
                THEN 'Source-text contamination'

            ELSE 'Usable supplier name'
        END AS supplier_name_quality
    FROM suppliers
),

supplier_allocations AS (
    SELECT
        a.supplier_key,
        SUM(
            CASE
                WHEN aw.award_value IS NOT NULL
                THEN aw.award_value / NULLIF(sc.supplier_count, 0)
                ELSE 0
            END
        ) AS allocated_award_value
    FROM award_suppliers a
    JOIN supplier_counts sc
        ON a.award_id = sc.award_id
    JOIN latest_awards aw
        ON a.award_id = aw.award_id
    GROUP BY a.supplier_key
),

usable_suppliers AS (
    SELECT
        sa.supplier_key,
        sa.allocated_award_value
    FROM supplier_allocations sa
    JOIN supplier_name_quality sq
        ON sa.supplier_key = sq.supplier_key
    WHERE sq.supplier_name_quality = 'Usable supplier name'
),

ranked_suppliers AS (
    SELECT
        supplier_key,
        allocated_award_value,
        ROW_NUMBER() OVER (
            ORDER BY allocated_award_value DESC
        ) AS supplier_rank,
        COUNT(*) OVER () AS total_suppliers
    FROM usable_suppliers
),

concentration AS (
    SELECT
        SUM(allocated_award_value) AS total_allocated_value,

        SUM(
            CASE
                WHEN supplier_rank <= CEIL(total_suppliers * 0.01)
                THEN allocated_award_value
                ELSE 0
            END
        ) AS top_1_value,

        SUM(
            CASE
                WHEN supplier_rank <= CEIL(total_suppliers * 0.05)
                THEN allocated_award_value
                ELSE 0
            END
        ) AS top_5_value,

        SUM(
            CASE
                WHEN supplier_rank <= CEIL(total_suppliers * 0.10)
                THEN allocated_award_value
                ELSE 0
            END
        ) AS top_10_value
    FROM ranked_suppliers
)

SELECT
    'Top 1%' AS supplier_group,
    ROUND(
        100.0 * top_1_value / NULLIF(total_allocated_value, 0),
        2
    ) AS allocated_award_value_share_pct
FROM concentration

UNION ALL

SELECT
    'Top 5%',
    ROUND(
        100.0 * top_5_value / NULLIF(total_allocated_value, 0),
        2
    )
FROM concentration

UNION ALL

SELECT
    'Top 10%',
    ROUND(
        100.0 * top_10_value / NULLIF(total_allocated_value, 0),
        2
    )
FROM concentration

UNION ALL

SELECT
    'Remaining 90%',
    ROUND(
        100.0 * (total_allocated_value - top_10_value)
        / NULLIF(total_allocated_value, 0),
        2
    )
FROM concentration;


-- ============================================================================
-- QUERY 17
-- LATEST AWARD VALUE BY PROCUREMENT CATEGORY
-- ============================================================================

SELECT
    COALESCE(p.procurement_category, 'Unknown') AS procurement_category,
    COUNT(DISTINCT a.award_id) AS award_count,
    SUM(
        CASE
            WHEN a.award_value IS NOT NULL THEN 1
            ELSE 0
        END
    ) AS awards_with_value,
    ROUND(
        SUM(COALESCE(a.award_value, 0)),
        2
    ) AS recorded_award_value
FROM award_versions a
JOIN procurements p
    ON a.ocid = p.ocid
WHERE a.is_latest_award_version = 1
  AND a.award_id IN (
      SELECT DISTINCT award_id
      FROM award_suppliers
  )
GROUP BY COALESCE(p.procurement_category, 'Unknown')
ORDER BY recorded_award_value DESC;


-- ============================================================================
-- QUERY 18
-- LATEST AWARD VALUE BY PROCUREMENT METHOD
-- ============================================================================

SELECT
    COALESCE(p.procurement_method, 'Unknown') AS procurement_method,
    COUNT(DISTINCT a.award_id) AS award_count,
    SUM(
        CASE
            WHEN a.award_value IS NOT NULL THEN 1
            ELSE 0
        END
    ) AS awards_with_value,
    ROUND(
        SUM(COALESCE(a.award_value, 0)),
        2
    ) AS recorded_award_value
FROM award_versions a
JOIN procurements p
    ON a.ocid = p.ocid
WHERE a.is_latest_award_version = 1
  AND a.award_id IN (
      SELECT DISTINCT award_id
      FROM award_suppliers
  )
GROUP BY COALESCE(p.procurement_method, 'Unknown')
ORDER BY recorded_award_value DESC;


-- ============================================================================
-- QUERY 19
-- LARGE SUPPLIER ALLOCATED-VALUE EXPOSURES FOR REVIEW
-- ============================================================================

WITH supplier_counts AS (
    SELECT
        award_id,
        COUNT(DISTINCT supplier_key) AS supplier_count
    FROM award_suppliers
    GROUP BY award_id
),

latest_awards AS (
    SELECT
        award_id,
        award_value
    FROM award_versions
    WHERE is_latest_award_version = 1
),

supplier_name_quality AS (
    SELECT
        supplier_key,
        canonical_supplier_name,
        identity_review_flag,
        CASE
            WHEN canonical_supplier_name IS NULL
                OR TRIM(canonical_supplier_name) = ''
                THEN 'Missing supplier name'

            WHEN LOWER(canonical_supplier_name) LIKE '%redacted%'
                OR LOWER(canonical_supplier_name) LIKE '%foia%'
                THEN 'Redacted / unavailable'

            WHEN LOWER(canonical_supplier_name) LIKE '%successful supplier%'
                OR LOWER(canonical_supplier_name) LIKE '%supplier list%'
                OR LOWER(canonical_supplier_name) LIKE '%see contracts finder%'
                OR LOWER(canonical_supplier_name) LIKE '%see webpage%'
                OR LOWER(canonical_supplier_name) LIKE '%contract award details%'
                OR LOWER(canonical_supplier_name) LIKE '%attachments%'
                THEN 'Source-text contamination'

            ELSE 'Usable supplier name'
        END AS supplier_name_quality
    FROM suppliers
),

supplier_allocations AS (
    SELECT
        a.supplier_key,
        SUM(
            CASE
                WHEN aw.award_value IS NOT NULL
                THEN aw.award_value / NULLIF(sc.supplier_count, 0)
                ELSE 0
            END
        ) AS allocated_award_value,
        COUNT(DISTINCT a.award_id) AS award_count
    FROM award_suppliers a
    JOIN supplier_counts sc
        ON a.award_id = sc.award_id
    JOIN latest_awards aw
        ON a.award_id = aw.award_id
    GROUP BY a.supplier_key
)

SELECT
    sa.supplier_key,
    sq.canonical_supplier_name,
    sa.award_count,
    ROUND(sa.allocated_award_value, 2)
        AS allocated_award_value,
    sq.identity_review_flag
FROM supplier_allocations sa
JOIN supplier_name_quality sq
    ON sa.supplier_key = sq.supplier_key
WHERE sq.supplier_name_quality = 'Usable supplier name'
  AND sa.allocated_award_value >= 1000000000
ORDER BY sa.allocated_award_value DESC
LIMIT 25;


-- ============================================================================
-- END OF SUPPLIER ANALYSIS
-- ============================================================================