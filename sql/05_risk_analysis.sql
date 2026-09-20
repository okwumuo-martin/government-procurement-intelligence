-- ============================================================
-- CONTRACTS FINDER 2025
-- PROCUREMENT RISK ANALYSIS
-- ============================================================
--
-- Purpose:
-- Identify procurement patterns that warrant further analytical
-- review based on observable characteristics in the dataset.
--
-- IMPORTANT:
-- These indicators are analytical screening signals.
-- They do not establish fraud, misconduct, overpayment,
-- or supplier wrongdoing.
--
-- Supplier award value allocation:
-- Where an award involves multiple suppliers, the recorded
-- award value is allocated equally across the associated
-- supplier relationships for supplier-level analysis.
-- This prevents double-counting of award value.
--
-- The allocation is an analytical assumption and should not
-- be interpreted as actual supplier payment or expenditure.
-- ============================================================

WITH latest_awards AS (
    SELECT
        av.award_id,
        av.release_id,
        av.ocid,
        av.release_date,
        av.award_date,
        av.award_status,
        av.award_value,
        av.award_currency,
        av.contract_start,
        av.contract_end
    FROM award_versions av
    WHERE av.is_latest_award_version = 1
),

award_supplier_counts AS (
    SELECT
        la.award_id,
        la.release_id,
        COUNT(DISTINCT aws.supplier_key) AS supplier_count
    FROM latest_awards la
    JOIN award_suppliers aws
        ON la.award_id = aws.award_id
       AND la.release_id = aws.release_id
    GROUP BY
        la.award_id,
        la.release_id
),

latest_award_supplier_base AS (
    SELECT
        la.award_id,
        la.release_id,
        la.ocid,
        la.release_date,
        la.award_date,
        la.award_status,
        la.award_value,
        la.award_currency,
        la.contract_start,
        la.contract_end,

        aws.supplier_key,
        aws.supplier_id,
        aws.supplier_name,
        aws.canonical_supplier_name,
        aws.supplier_id_quality,
        aws.identity_review_flag,

        p.buyer_name,
        p.buyer_id,
        p.procurement_method,
        p.procurement_category,
        p.tender_value,

        ascnt.supplier_count,

        CASE
            WHEN la.award_value IS NOT NULL
                 AND ascnt.supplier_count > 0
            THEN la.award_value / ascnt.supplier_count
            ELSE NULL
        END AS allocated_award_value

    FROM latest_awards la

    JOIN award_suppliers aws
        ON la.award_id = aws.award_id
       AND la.release_id = aws.release_id

    JOIN award_supplier_counts ascnt
        ON la.award_id = ascnt.award_id
       AND la.release_id = ascnt.release_id

    LEFT JOIN procurements p
        ON la.ocid = p.ocid
)

-- ============================================================
-- QUERY 1: RISK ANALYSIS POPULATION
-- ============================================================

SELECT
    COUNT(*) AS supplier_award_relationships,
    COUNT(DISTINCT award_id) AS unique_awards,
    COUNT(DISTINCT ocid) AS unique_procurements,

    SUM(
        CASE
            WHEN award_value IS NOT NULL THEN 1
            ELSE 0
        END
    ) AS awards_with_value,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN award_value IS NOT NULL THEN 1
                ELSE 0
            END
        )
        / COUNT(*),
        2
    ) AS value_completeness_pct

FROM latest_award_supplier_base;

-- ============================================================
-- QUERY 2: HIGH-VALUE AWARDS
-- ============================================================

WITH latest_awards AS (
    SELECT *
    FROM award_versions
    WHERE is_latest_award_version = 1
)

SELECT
    award_id,
    release_id,
    ocid,
    award_date,
    award_value,
    award_currency,
    award_status,
    contract_start,
    contract_end
FROM latest_awards
WHERE award_value >= 100000000
ORDER BY award_value DESC
LIMIT 25;

WITH latest_awards AS (
    SELECT *
    FROM award_versions
    WHERE is_latest_award_version = 1
),

high_value_procurements AS (
    SELECT
        av.ocid,
        p.buyer_name,
        p.procurement_category,
        p.procurement_method,
        COUNT(DISTINCT av.award_id) AS award_count,
        SUM(av.award_value) AS total_recorded_award_value
    FROM latest_awards av
    LEFT JOIN procurements p
        ON av.ocid = p.ocid
    WHERE av.award_value >= 100000000
    GROUP BY
        av.ocid,
        p.buyer_name,
        p.procurement_category,
        p.procurement_method
)

SELECT
    ocid,
    buyer_name,
    procurement_category,
    procurement_method,
    award_count,
    total_recorded_award_value
FROM high_value_procurements
ORDER BY total_recorded_award_value DESC
LIMIT 25;

-- ============================================================
-- QUERY 3: HIGH-VALUE AWARDS BY PROCUREMENT METHOD
-- ============================================================

WITH latest_awards AS (
    SELECT *
    FROM award_versions
    WHERE is_latest_award_version = 1
)

SELECT
    COALESCE(p.procurement_method, 'Unknown') AS procurement_method,

    COUNT(*) AS high_value_awards,

    SUM(
        CASE
            WHEN av.award_value IS NOT NULL
            THEN av.award_value
            ELSE 0
        END
    ) AS recorded_award_value

FROM latest_awards av

LEFT JOIN procurements p
    ON av.ocid = p.ocid

WHERE av.award_value >= 100000000

GROUP BY
    COALESCE(p.procurement_method, 'Unknown')

ORDER BY
    recorded_award_value DESC;

-- ============================================================
-- QUERY 4: HIGH-VALUE DIRECT AWARDS
-- ============================================================

WITH latest_awards AS (
    SELECT *
    FROM award_versions
    WHERE is_latest_award_version = 1
)

SELECT
    av.award_id,
    av.release_id,
    av.ocid,
    p.buyer_name,
    p.procurement_category,
    p.procurement_method,
    av.award_date,
    av.award_value,
    av.award_currency,
    av.contract_start,
    av.contract_end

FROM latest_awards av

LEFT JOIN procurements p
    ON av.ocid = p.ocid

WHERE LOWER(TRIM(p.procurement_method)) = 'direct'
  AND av.award_value >= 100000000

ORDER BY
    av.award_value DESC

LIMIT 25;

-- ============================================================
-- QUERY 5: DIRECT PROCUREMENT EXPOSURE
-- ============================================================

WITH latest_awards AS (
    SELECT *
    FROM award_versions
    WHERE is_latest_award_version = 1
)

SELECT
    COALESCE(p.procurement_method, 'Unknown') AS procurement_method,

    COUNT(*) AS award_count,

    COUNT(
        CASE
            WHEN av.award_value IS NOT NULL
            THEN 1
        END
    ) AS awards_with_value,

    ROUND(
        100.0 *
        COUNT(
            CASE
                WHEN av.award_value IS NOT NULL
                THEN 1
            END
        )
        / COUNT(*),
        2
    ) AS value_completeness_pct,

    SUM(
        COALESCE(av.award_value, 0)
    ) AS recorded_award_value

FROM latest_awards av

LEFT JOIN procurements p
    ON av.ocid = p.ocid

GROUP BY
    COALESCE(p.procurement_method, 'Unknown')

ORDER BY
    recorded_award_value DESC;

-- ============================================================
-- QUERY 6: BUYER-SUPPLIER DEPENDENCY
-- ============================================================

WITH latest_awards AS (
    SELECT *
    FROM award_versions
    WHERE is_latest_award_version = 1
),

latest_relationships AS (
    SELECT
        la.award_id,
        la.release_id,
        la.ocid,
        aws.supplier_key,
        aws.canonical_supplier_name,
        p.buyer_name
    FROM latest_awards la

    JOIN award_suppliers aws
        ON la.award_id = aws.award_id
       AND la.release_id = aws.release_id

    LEFT JOIN procurements p
        ON la.ocid = p.ocid

    WHERE aws.canonical_supplier_name IS NOT NULL
),

buyer_supplier_awards AS (
    SELECT
        buyer_name,
        supplier_key,
        canonical_supplier_name,
        COUNT(DISTINCT award_id) AS supplier_awards
    FROM latest_relationships
    WHERE buyer_name IS NOT NULL
    GROUP BY
        buyer_name,
        supplier_key,
        canonical_supplier_name
),

buyer_totals AS (
    SELECT
        buyer_name,
        SUM(supplier_awards) AS total_supplier_awards
    FROM buyer_supplier_awards
    GROUP BY buyer_name
),

ranked_suppliers AS (
    SELECT
        bsa.*,
        bt.total_supplier_awards,

        ROW_NUMBER() OVER (
            PARTITION BY bsa.buyer_name
            ORDER BY bsa.supplier_awards DESC
        ) AS supplier_rank

    FROM buyer_supplier_awards bsa

    JOIN buyer_totals bt
        ON bsa.buyer_name = bt.buyer_name
)

SELECT
    buyer_name,
    canonical_supplier_name,
    supplier_awards,
    total_supplier_awards,

    ROUND(
        100.0 * supplier_awards / total_supplier_awards,
        2
    ) AS top_supplier_award_share_pct

FROM ranked_suppliers

WHERE supplier_rank = 1
  AND total_supplier_awards >= 5

ORDER BY
    top_supplier_award_share_pct DESC,
    total_supplier_awards DESC

LIMIT 25;

-- ============================================================
-- QUERY 8
-- High-value procurement structures and supplier participation
-- ============================================================

WITH latest_awards AS (
    SELECT *
    FROM award_versions
    WHERE is_latest_award_version = 1
),

high_value_procurements AS (
    SELECT
        av.ocid,
        p.buyer_name,
        p.procurement_category,
        p.procurement_method,
        COUNT(DISTINCT av.award_id) AS award_count,
        SUM(av.award_value) AS total_recorded_award_value
    FROM latest_awards av
    LEFT JOIN procurements p
        ON av.ocid = p.ocid
    WHERE av.award_value >= 100000000
    GROUP BY
        av.ocid,
        p.buyer_name,
        p.procurement_category,
        p.procurement_method
),

supplier_summary AS (
    SELECT
        la.ocid,
        COUNT(DISTINCT aws.supplier_key) AS supplier_count,
        GROUP_CONCAT(
            DISTINCT aws.canonical_supplier_name
        ) AS supplier_names
    FROM latest_awards la
    JOIN award_suppliers aws
        ON la.award_id = aws.award_id
       AND la.release_id = aws.release_id
    WHERE aws.canonical_supplier_name IS NOT NULL
    GROUP BY la.ocid
)

SELECT
    hv.ocid,
    hv.buyer_name,
    hv.procurement_category,
    hv.procurement_method,
    hv.award_count,
    hv.total_recorded_award_value,
    COALESCE(ss.supplier_count, 0) AS supplier_count,
    ss.supplier_names
FROM high_value_procurements hv
LEFT JOIN supplier_summary ss
    ON hv.ocid = ss.ocid
ORDER BY hv.total_recorded_award_value DESC
LIMIT 25;

-- ============================================================
-- QUERY 9
-- Contract duration profile
-- ============================================================

WITH latest_awards AS (
    SELECT
        award_id,
        release_id,
        ocid,
        award_value,
        contract_start,
        contract_end
    FROM award_versions
    WHERE is_latest_award_version = 1
),

contract_durations AS (
    SELECT
        award_id,
        release_id,
        ocid,
        award_value,
        contract_start,
        contract_end,
        ROUND(
            julianday(contract_end) - julianday(contract_start),
            1
        ) AS duration_days,
        ROUND(
            (julianday(contract_end) - julianday(contract_start)) / 365.25,
            2
        ) AS duration_years
    FROM latest_awards
    WHERE contract_start IS NOT NULL
      AND contract_end IS NOT NULL
      AND julianday(contract_end) >= julianday(contract_start)
)

SELECT
    COUNT(*) AS awards_with_contract_dates,
    ROUND(AVG(duration_days), 1) AS average_duration_days,
    ROUND(AVG(duration_years), 2) AS average_duration_years,
    MIN(duration_days) AS minimum_duration_days,
    MAX(duration_days) AS maximum_duration_days,

    SUM(
        CASE
            WHEN duration_years >= 1 THEN 1
            ELSE 0
        END
    ) AS contracts_1_year_or_more,

    SUM(
        CASE
            WHEN duration_years >= 3 THEN 1
            ELSE 0
        END
    ) AS contracts_3_years_or_more,

    SUM(
        CASE
            WHEN duration_years >= 5 THEN 1
            ELSE 0
        END
    ) AS contracts_5_years_or_more,

    SUM(
        CASE
            WHEN duration_years >= 10 THEN 1
            ELSE 0
        END
    ) AS contracts_10_years_or_more

FROM contract_durations;

-- ============================================================
-- QUERY 10
-- Longest contract durations
-- ============================================================

WITH latest_awards AS (
    SELECT
        award_id,
        release_id,
        ocid,
        award_date,
        award_value,
        award_currency,
        contract_start,
        contract_end
    FROM award_versions
    WHERE is_latest_award_version = 1
),

contract_durations AS (
    SELECT
        av.award_id,
        av.release_id,
        av.ocid,
        av.award_date,
        av.award_value,
        av.award_currency,
        av.contract_start,
        av.contract_end,

        ROUND(
            (julianday(av.contract_end) -
             julianday(av.contract_start)) / 365.25,
            2
        ) AS duration_years

    FROM latest_awards av

    WHERE av.contract_start IS NOT NULL
      AND av.contract_end IS NOT NULL
      AND julianday(av.contract_end) >=
          julianday(av.contract_start)
)

SELECT
    cd.award_id,
    cd.ocid,
    p.buyer_name,
    p.procurement_category,
    p.procurement_method,
    cd.award_date,
    cd.award_value,
    cd.award_currency,
    cd.contract_start,
    cd.contract_end,
    cd.duration_years

FROM contract_durations cd

LEFT JOIN procurements p
    ON cd.ocid = p.ocid

ORDER BY cd.duration_years DESC

LIMIT 25;

-- ============================================================
-- QUERY 11
-- High-value and long-duration procurement review candidates
-- ============================================================

WITH latest_awards AS (
    SELECT
        award_id,
        release_id,
        ocid,
        award_date,
        award_value,
        award_currency,
        contract_start,
        contract_end
    FROM award_versions
    WHERE is_latest_award_version = 1
),

contract_profiles AS (
    SELECT
        av.award_id,
        av.release_id,
        av.ocid,
        av.award_date,
        av.award_value,
        av.award_currency,
        av.contract_start,
        av.contract_end,

        ROUND(
            (julianday(av.contract_end) -
             julianday(av.contract_start)) / 365.25,
            2
        ) AS duration_years

    FROM latest_awards av

    WHERE av.contract_start IS NOT NULL
      AND av.contract_end IS NOT NULL
      AND julianday(av.contract_end) >=
          julianday(av.contract_start)
)

SELECT
    cp.award_id,
    cp.ocid,
    p.buyer_name,
    p.procurement_category,
    p.procurement_method,
    cp.award_date,
    cp.award_value,
    cp.award_currency,
    cp.contract_start,
    cp.contract_end,
    cp.duration_years

FROM contract_profiles cp

LEFT JOIN procurements p
    ON cp.ocid = p.ocid

WHERE cp.award_value >= 100000000
  AND cp.duration_years >= 10

ORDER BY
    cp.award_value DESC,
    cp.duration_years DESC

LIMIT 25;

-- ============================================================
-- QUERY 12
-- HIGH-VALUE + LONG-DURATION + PROCUREMENT METHOD + SUPPLIER
-- PARTICIPATION
-- ============================================================

WITH latest_awards AS (
    SELECT
        award_id,
        release_id,
        ocid,
        award_date,
        award_value,
        award_currency,
        contract_start,
        contract_end
    FROM award_versions
    WHERE is_latest_award_version = 1
),

contract_profiles AS (
    SELECT
        av.award_id,
        av.release_id,
        av.ocid,
        av.award_date,
        av.award_value,
        av.award_currency,
        av.contract_start,
        av.contract_end,

        ROUND(
            (julianday(av.contract_end) -
             julianday(av.contract_start)) / 365.25,
            2
        ) AS duration_years

    FROM latest_awards av

    WHERE av.contract_start IS NOT NULL
      AND av.contract_end IS NOT NULL
      AND julianday(av.contract_end) >= julianday(av.contract_start)
),

supplier_summary AS (
    SELECT
        aws.award_id,
        aws.release_id,

        COUNT(
            DISTINCT CASE
                WHEN aws.canonical_supplier_name IS NOT NULL
                THEN aws.supplier_key
            END
        ) AS identifiable_supplier_count,

        COUNT(
            DISTINCT CASE
                WHEN aws.identity_review_flag = 1
                THEN aws.supplier_key
            END
        ) AS supplier_identity_review_count,

        MAX(
            CASE
                WHEN aws.supplier_id_quality = 'unreliable_or_missing'
                THEN 1
                ELSE 0
            END
        ) AS has_unreliable_supplier_id

    FROM award_suppliers aws

    GROUP BY
        aws.award_id,
        aws.release_id
)

SELECT
    cp.award_id,
    cp.ocid,

    p.buyer_name,
    p.procurement_category,
    p.procurement_method,

    cp.award_date,
    cp.award_value,
    cp.award_currency,

    cp.contract_start,
    cp.contract_end,
    cp.duration_years,

    COALESCE(
        ss.identifiable_supplier_count,
        0
    ) AS identifiable_supplier_count,

    COALESCE(
        ss.supplier_identity_review_count,
        0
    ) AS supplier_identity_review_count,

    COALESCE(
        ss.has_unreliable_supplier_id,
        0
    ) AS has_unreliable_supplier_id,

    CASE
        WHEN cp.award_value >= 1000000000
             AND cp.duration_years >= 10
             AND LOWER(COALESCE(p.procurement_method, '')) IN ('direct', 'limited')
            THEN 'Priority review'

        WHEN cp.award_value >= 500000000
             AND cp.duration_years >= 10
            THEN 'High review'

        WHEN cp.award_value >= 100000000
             AND cp.duration_years >= 10
            THEN 'Moderate review'

        ELSE 'Contextual review'
    END AS review_category

FROM contract_profiles cp

LEFT JOIN procurements p
    ON cp.ocid = p.ocid

LEFT JOIN supplier_summary ss
    ON cp.award_id = ss.award_id
   AND cp.release_id = ss.release_id

WHERE cp.award_value >= 100000000
  AND cp.duration_years >= 10

ORDER BY
    CASE
        WHEN cp.award_value >= 1000000000
             AND cp.duration_years >= 10
             AND LOWER(COALESCE(p.procurement_method, '')) IN ('direct', 'limited')
            THEN 1

        WHEN cp.award_value >= 500000000
             AND cp.duration_years >= 10
            THEN 2

        ELSE 3
    END,

    cp.award_value DESC,
    cp.duration_years DESC

LIMIT 50;

-- ============================================================
-- QUERY 13
-- PROCUREMENT REVIEW INDICATOR (PRI)
-- ============================================================

WITH latest_awards AS (
    SELECT
        award_id,
        release_id,
        ocid,
        award_date,
        award_value,
        award_currency,
        contract_start,
        contract_end
    FROM award_versions
    WHERE is_latest_award_version = 1
),

contract_profiles AS (
    SELECT
        av.award_id,
        av.release_id,
        av.ocid,
        av.award_date,
        av.award_value,
        av.award_currency,
        av.contract_start,
        av.contract_end,

        ROUND(
            (
                julianday(av.contract_end) -
                julianday(av.contract_start)
            ) / 365.25,
            2
        ) AS duration_years

    FROM latest_awards av

    WHERE av.contract_start IS NOT NULL
      AND av.contract_end IS NOT NULL
      AND julianday(av.contract_end) >= julianday(av.contract_start)
),

supplier_summary AS (
    SELECT
        aws.award_id,
        aws.release_id,

        COUNT(
            DISTINCT CASE
                WHEN aws.canonical_supplier_name IS NOT NULL
                 AND aws.supplier_identity_flag = 0
                THEN aws.supplier_key
            END
        ) AS usable_supplier_count,

        MAX(
            CASE
                WHEN aws.identity_review_flag = 1
                THEN 1
                ELSE 0
            END
        ) AS supplier_identity_review_flag,

        MAX(
            CASE
                WHEN aws.supplier_id_quality = 'unreliable_or_missing'
                THEN 1
                ELSE 0
            END
        ) AS unreliable_supplier_id_flag

    FROM award_suppliers aws

    GROUP BY
        aws.award_id,
        aws.release_id
),

base AS (
    SELECT
        cp.award_id,
        cp.release_id,
        cp.ocid,

        p.buyer_name,
        p.procurement_category,
        p.procurement_method,

        cp.award_date,
        cp.award_value,
        cp.award_currency,

        cp.contract_start,
        cp.contract_end,
        cp.duration_years,

        COALESCE(
            ss.usable_supplier_count,
            0
        ) AS usable_supplier_count,

        COALESCE(
            ss.supplier_identity_review_flag,
            0
        ) AS supplier_identity_review_flag,

        COALESCE(
            ss.unreliable_supplier_id_flag,
            0
        ) AS unreliable_supplier_id_flag

    FROM contract_profiles cp

    LEFT JOIN procurements p
        ON cp.ocid = p.ocid

    LEFT JOIN supplier_summary ss
        ON cp.award_id = ss.award_id
       AND cp.release_id = ss.release_id
),

scored AS (
    SELECT
        *,

        CASE
            WHEN award_value >= 1000000000 THEN 3
            WHEN award_value >= 100000000 THEN 2
            ELSE 0
        END AS value_points,

        CASE
            WHEN duration_years >= 20 THEN 2
            WHEN duration_years >= 10 THEN 1
            ELSE 0
        END AS duration_points,

        CASE
            WHEN LOWER(COALESCE(procurement_method, '')) = 'direct'
                THEN 2

            WHEN LOWER(COALESCE(procurement_method, '')) = 'limited'
                THEN 1

            ELSE 0
        END AS method_points,

        CASE
            WHEN usable_supplier_count = 1 THEN 1
            ELSE 0
        END AS single_supplier_points,

        CASE
            WHEN supplier_identity_review_flag = 1
              OR unreliable_supplier_id_flag = 1
                THEN 1
            ELSE 0
        END AS supplier_data_quality_points

    FROM base
),

final_scored AS (
    SELECT
        *,

        (
            value_points +
            duration_points +
            method_points +
            single_supplier_points +
            supplier_data_quality_points
        ) AS pri_score

    FROM scored
)

SELECT
    award_id,
    release_id,
    ocid,

    buyer_name,
    procurement_category,
    procurement_method,

    award_date,
    award_value,
    award_currency,

    contract_start,
    contract_end,
    duration_years,

    usable_supplier_count,

    supplier_identity_review_flag,
    unreliable_supplier_id_flag,

    value_points,
    duration_points,
    method_points,
    single_supplier_points,
    supplier_data_quality_points,

    pri_score,

    CASE
        WHEN pri_score >= 7
            THEN 'Priority review'

        WHEN pri_score >= 5
            THEN 'High review'

        WHEN pri_score >= 3
            THEN 'Moderate review'

        ELSE 'Lower review priority'
    END AS pri_category,

    CASE
        WHEN pri_score >= 7
            THEN 'Multiple high-priority screening signals'

        WHEN pri_score >= 5
            THEN 'Several material screening signals'

        WHEN pri_score >= 3
            THEN 'At least one material screening signal'

        ELSE 'Limited screening signals'
    END AS review_rationale

FROM final_scored

ORDER BY
    pri_score DESC,
    award_value DESC,
    duration_years DESC;

-- ============================================================
-- QUERY 14
-- PROCUREMENT REVIEW INDICATOR V2
-- ============================================================

WITH latest_awards AS (
    SELECT
        award_id,
        release_id,
        ocid,
        award_date,
        award_value,
        award_currency,
        contract_start,
        contract_end
    FROM award_versions
    WHERE is_latest_award_version = 1
),

contract_profiles AS (
    SELECT
        av.award_id,
        av.release_id,
        av.ocid,
        av.award_date,
        av.award_value,
        av.award_currency,
        av.contract_start,
        av.contract_end,

        ROUND(
            (
                julianday(av.contract_end) -
                julianday(av.contract_start)
            ) / 365.25,
            2
        ) AS duration_years

    FROM latest_awards av

    WHERE av.contract_start IS NOT NULL
      AND av.contract_end IS NOT NULL
      AND julianday(av.contract_end) >= julianday(av.contract_start)
),

supplier_summary AS (
    SELECT
        aws.award_id,
        aws.release_id,

        COUNT(
            DISTINCT CASE
                WHEN aws.supplier_key IS NOT NULL
                 AND aws.canonical_supplier_name IS NOT NULL
                 AND LOWER(
                     COALESCE(
                         aws.canonical_supplier_name,
                         ''
                     )
                 ) NOT LIKE '%successful supplier%'
                 AND LOWER(
                     COALESCE(
                         aws.canonical_supplier_name,
                         ''
                     )
                 ) NOT LIKE '%supplier list%'
                 AND LOWER(
                     COALESCE(
                         aws.canonical_supplier_name,
                         ''
                     )
                 ) NOT LIKE '%see webpage%'
                 AND LOWER(
                     COALESCE(
                         aws.canonical_supplier_name,
                         ''
                     )
                 ) NOT LIKE '%contract award details%'
                 AND LOWER(
                     COALESCE(
                         aws.canonical_supplier_name,
                         ''
                     )
                 ) NOT LIKE '%attachments%'
                THEN aws.supplier_key
            END
        ) AS usable_supplier_count,

        MAX(
            CASE
                WHEN aws.supplier_identity_flag =
                     'id_multiple_names_review'
                THEN 1
                ELSE 0
            END
        ) AS supplier_identity_review_flag,

        MAX(
            CASE
                WHEN aws.supplier_id_quality =
                     'unreliable_or_missing'
                THEN 1
                ELSE 0
            END
        ) AS unreliable_supplier_id_flag,

        MAX(
            CASE
                WHEN aws.canonical_supplier_name IS NOT NULL
                 AND LOWER(
                     COALESCE(
                         aws.canonical_supplier_name,
                         ''
                     )
                 ) LIKE '%successful supplier%'
                THEN 1
                ELSE 0
            END
        ) AS supplier_reference_text_flag

    FROM award_suppliers aws

    GROUP BY
        aws.award_id,
        aws.release_id
),

base AS (
    SELECT
        cp.award_id,
        cp.release_id,
        cp.ocid,

        p.buyer_name,
        p.procurement_category,
        p.procurement_method,

        cp.award_date,
        cp.award_value,
        cp.award_currency,

        cp.contract_start,
        cp.contract_end,
        cp.duration_years,

        COALESCE(
            ss.usable_supplier_count,
            0
        ) AS usable_supplier_count,

        COALESCE(
            ss.supplier_identity_review_flag,
            0
        ) AS supplier_identity_review_flag,

        COALESCE(
            ss.unreliable_supplier_id_flag,
            0
        ) AS unreliable_supplier_id_flag,

        COALESCE(
            ss.supplier_reference_text_flag,
            0
        ) AS supplier_reference_text_flag

    FROM contract_profiles cp

    LEFT JOIN procurements p
        ON cp.ocid = p.ocid

    LEFT JOIN supplier_summary ss
        ON cp.award_id = ss.award_id
       AND cp.release_id = ss.release_id
),

scored AS (
    SELECT
        *,

        CASE
            WHEN award_value >= 1000000000 THEN 3
            WHEN award_value >= 100000000 THEN 2
            ELSE 0
        END AS value_points,

        CASE
            WHEN duration_years >= 20 THEN 2
            WHEN duration_years >= 10 THEN 1
            ELSE 0
        END AS duration_points,

        CASE
            WHEN LOWER(
                COALESCE(procurement_method, '')
            ) = 'direct'
                THEN 2

            WHEN LOWER(
                COALESCE(procurement_method, '')
            ) = 'limited'
                THEN 1

            ELSE 0
        END AS method_points,

        CASE
            WHEN usable_supplier_count = 1
                THEN 1
            ELSE 0
        END AS single_supplier_points

    FROM base
),

final_scored AS (
    SELECT
        *,

        (
            value_points +
            duration_points +
            method_points +
            single_supplier_points
        ) AS pri_score

    FROM scored
)

SELECT
    award_id,
    release_id,
    ocid,

    buyer_name,
    procurement_category,
    procurement_method,

    award_date,
    award_value,
    award_currency,

    contract_start,
    contract_end,
    duration_years,

    usable_supplier_count,

    supplier_identity_review_flag,
    unreliable_supplier_id_flag,
    supplier_reference_text_flag,

    value_points,
    duration_points,
    method_points,
    single_supplier_points,

    pri_score,

    CASE
        WHEN pri_score >= 6
            THEN 'Priority review'

        WHEN pri_score >= 4
            THEN 'High review'

        WHEN pri_score >= 2
            THEN 'Moderate review'

        ELSE 'Lower review priority'
    END AS pri_category,

    CASE
        WHEN pri_score >= 6
            THEN 'Multiple material screening signals'

        WHEN pri_score >= 4
            THEN 'Several material screening signals'

        WHEN pri_score >= 2
            THEN 'At least one material screening signal'

        ELSE 'Limited screening signals'
    END AS review_rationale

FROM final_scored

ORDER BY
    pri_score DESC,
    award_value DESC,
    duration_years DESC;

-- ============================================================
-- QUERY 15
-- PROCUREMENT REVIEW INDICATOR V2
-- VALIDATION SUMMARY
-- ============================================================

WITH pri AS (
    SELECT
        pri_score,
        pri_category,
        usable_supplier_count,
        supplier_identity_review_flag,
        unreliable_supplier_id_flag,
        supplier_reference_text_flag,
        award_value,
        duration_years,
        method_points,
        single_supplier_points
    FROM (
        WITH latest_awards AS (
            SELECT
                award_id,
                release_id,
                ocid,
                award_date,
                award_value,
                award_currency,
                contract_start,
                contract_end
            FROM award_versions
            WHERE is_latest_award_version = 1
        ),

        contract_profiles AS (
            SELECT
                av.award_id,
                av.release_id,
                av.ocid,
                av.award_date,
                av.award_value,
                av.award_currency,
                av.contract_start,
                av.contract_end,

                ROUND(
                    (
                        julianday(av.contract_end) -
                        julianday(av.contract_start)
                    ) / 365.25,
                    2
                ) AS duration_years

            FROM latest_awards av

            WHERE av.contract_start IS NOT NULL
              AND av.contract_end IS NOT NULL
              AND julianday(av.contract_end) >=
                  julianday(av.contract_start)
        ),

        supplier_summary AS (
            SELECT
                aws.award_id,
                aws.release_id,

                COUNT(
                    DISTINCT CASE
                        WHEN aws.supplier_key IS NOT NULL
                         AND aws.canonical_supplier_name IS NOT NULL
                         AND LOWER(
                             COALESCE(
                                 aws.canonical_supplier_name,
                                 ''
                             )
                         ) NOT LIKE '%successful supplier%'
                         AND LOWER(
                             COALESCE(
                                 aws.canonical_supplier_name,
                                 ''
                             )
                         ) NOT LIKE '%supplier list%'
                         AND LOWER(
                             COALESCE(
                                 aws.canonical_supplier_name,
                                 ''
                             )
                         ) NOT LIKE '%see webpage%'
                         AND LOWER(
                             COALESCE(
                                 aws.canonical_supplier_name,
                                 ''
                             )
                         ) NOT LIKE '%contract award details%'
                         AND LOWER(
                             COALESCE(
                                 aws.canonical_supplier_name,
                                 ''
                             )
                         ) NOT LIKE '%attachments%'
                        THEN aws.supplier_key
                    END
                ) AS usable_supplier_count,

                MAX(
                    CASE
                        WHEN aws.supplier_identity_flag =
                             'id_multiple_names_review'
                        THEN 1
                        ELSE 0
                    END
                ) AS supplier_identity_review_flag,

                MAX(
                    CASE
                        WHEN aws.supplier_id_quality =
                             'unreliable_or_missing'
                        THEN 1
                        ELSE 0
                    END
                ) AS unreliable_supplier_id_flag,

                MAX(
                    CASE
                        WHEN aws.canonical_supplier_name IS NOT NULL
                         AND LOWER(
                             COALESCE(
                                 aws.canonical_supplier_name,
                                 ''
                             )
                         ) LIKE '%successful supplier%'
                        THEN 1
                        ELSE 0
                    END
                ) AS supplier_reference_text_flag

            FROM award_suppliers aws

            GROUP BY
                aws.award_id,
                aws.release_id
        ),

        base AS (
            SELECT
                cp.award_id,
                cp.release_id,
                cp.ocid,

                cp.award_date,
                cp.award_value,
                cp.award_currency,

                cp.contract_start,
                cp.contract_end,
                cp.duration_years,

                COALESCE(
                    ss.usable_supplier_count,
                    0
                ) AS usable_supplier_count,

                COALESCE(
                    ss.supplier_identity_review_flag,
                    0
                ) AS supplier_identity_review_flag,

                COALESCE(
                    ss.unreliable_supplier_id_flag,
                    0
                ) AS unreliable_supplier_id_flag,

                COALESCE(
                    ss.supplier_reference_text_flag,
                    0
                ) AS supplier_reference_text_flag,

                p.procurement_method

            FROM contract_profiles cp

            LEFT JOIN procurements p
                ON cp.ocid = p.ocid

            LEFT JOIN supplier_summary ss
                ON cp.award_id = ss.award_id
               AND cp.release_id = ss.release_id
        ),

        scored AS (
            SELECT
                *,

                CASE
                    WHEN award_value >= 1000000000 THEN 3
                    WHEN award_value >= 100000000 THEN 2
                    ELSE 0
                END AS value_points,

                CASE
                    WHEN duration_years >= 20 THEN 2
                    WHEN duration_years >= 10 THEN 1
                    ELSE 0
                END AS duration_points,

                CASE
                    WHEN LOWER(
                        COALESCE(procurement_method, '')
                    ) = 'direct'
                        THEN 2

                    WHEN LOWER(
                        COALESCE(procurement_method, '')
                    ) = 'limited'
                        THEN 1

                    ELSE 0
                END AS method_points,

                CASE
                    WHEN usable_supplier_count = 1
                        THEN 1
                    ELSE 0
                END AS single_supplier_points

            FROM base
        ),

        final_scored AS (
            SELECT
                *,

                (
                    value_points +
                    duration_points +
                    method_points +
                    single_supplier_points
                ) AS pri_score

            FROM scored
        )

        SELECT
            *,
            CASE
                WHEN pri_score >= 6
                    THEN 'Priority review'

                WHEN pri_score >= 4
                    THEN 'High review'

                WHEN pri_score >= 2
                    THEN 'Moderate review'

                ELSE 'Lower review priority'
            END AS pri_category

        FROM final_scored
    )
)

SELECT
    COUNT(*) AS total_records,

    SUM(
        CASE
            WHEN pri_category = 'Priority review'
            THEN 1 ELSE 0
        END
    ) AS priority_review,

    SUM(
        CASE
            WHEN pri_category = 'High review'
            THEN 1 ELSE 0
        END
    ) AS high_review,

    SUM(
        CASE
            WHEN pri_category = 'Moderate review'
            THEN 1 ELSE 0
        END
    ) AS moderate_review,

    SUM(
        CASE
            WHEN pri_category = 'Lower review priority'
            THEN 1 ELSE 0
        END
    ) AS lower_review,

    SUM(
        CASE WHEN pri_score = 0 THEN 1 ELSE 0 END
    ) AS score_0,

    SUM(
        CASE WHEN pri_score = 1 THEN 1 ELSE 0 END
    ) AS score_1,

    SUM(
        CASE WHEN pri_score = 2 THEN 1 ELSE 0 END
    ) AS score_2,

    SUM(
        CASE WHEN pri_score = 3 THEN 1 ELSE 0 END
    ) AS score_3,

    SUM(
        CASE WHEN pri_score = 4 THEN 1 ELSE 0 END
    ) AS score_4,

    SUM(
        CASE WHEN pri_score = 5 THEN 1 ELSE 0 END
    ) AS score_5,

    SUM(
        CASE WHEN pri_score = 6 THEN 1 ELSE 0 END
    ) AS score_6,

    SUM(
        CASE WHEN pri_score = 7 THEN 1 ELSE 0 END
    ) AS score_7,

    SUM(
        CASE WHEN pri_score = 8 THEN 1 ELSE 0 END
    ) AS score_8,

    SUM(
        CASE
            WHEN usable_supplier_count = 1
            THEN 1 ELSE 0
        END
    ) AS single_usable_supplier,

    SUM(
        CASE
            WHEN usable_supplier_count > 1
            THEN 1 ELSE 0
        END
    ) AS multiple_usable_suppliers,

    SUM(
        CASE
            WHEN usable_supplier_count = 0
            THEN 1 ELSE 0
        END
    ) AS no_usable_supplier,

    SUM(
        CASE
            WHEN supplier_identity_review_flag = 1
            THEN 1 ELSE 0
        END
    ) AS supplier_identity_review_records,

    SUM(
        CASE
            WHEN unreliable_supplier_id_flag = 1
            THEN 1 ELSE 0
        END
    ) AS unreliable_supplier_id_records,

    SUM(
        CASE
            WHEN supplier_reference_text_flag = 1
            THEN 1 ELSE 0
        END
    ) AS supplier_reference_text_records,

    SUM(
        CASE
            WHEN method_points > 0
            THEN 1 ELSE 0
        END
    ) AS procurement_method_points,

    SUM(
        CASE
            WHEN single_supplier_points > 0
            THEN 1 ELSE 0
        END
    ) AS single_supplier_points_records

FROM pri;

-- ============================================================
-- QUERY 16
-- HIGH / PRIORITY PROCUREMENT REVIEW POPULATION
-- ============================================================

WITH latest_awards AS (
    SELECT
        award_id,
        release_id,
        ocid,
        award_date,
        award_value,
        award_currency,
        contract_start,
        contract_end
    FROM award_versions
    WHERE is_latest_award_version = 1
),

contract_profiles AS (
    SELECT
        av.award_id,
        av.release_id,
        av.ocid,
        av.award_date,
        av.award_value,
        av.award_currency,
        av.contract_start,
        av.contract_end,

        ROUND(
            (
                julianday(av.contract_end) -
                julianday(av.contract_start)
            ) / 365.25,
            2
        ) AS duration_years

    FROM latest_awards av

    WHERE av.contract_start IS NOT NULL
      AND av.contract_end IS NOT NULL
      AND julianday(av.contract_end) >=
          julianday(av.contract_start)
),

supplier_summary AS (
    SELECT
        aws.award_id,
        aws.release_id,

        COUNT(
            DISTINCT CASE
                WHEN aws.supplier_key IS NOT NULL
                 AND aws.canonical_supplier_name IS NOT NULL

                 AND LOWER(
                     COALESCE(
                         aws.canonical_supplier_name,
                         ''
                     )
                 ) NOT LIKE '%successful supplier%'

                 AND LOWER(
                     COALESCE(
                         aws.canonical_supplier_name,
                         ''
                     )
                 ) NOT LIKE '%supplier list%'

                 AND LOWER(
                     COALESCE(
                         aws.canonical_supplier_name,
                         ''
                     )
                 ) NOT LIKE '%see webpage%'

                 AND LOWER(
                     COALESCE(
                         aws.canonical_supplier_name,
                         ''
                     )
                 ) NOT LIKE '%contract award details%'

                 AND LOWER(
                     COALESCE(
                         aws.canonical_supplier_name,
                         ''
                     )
                 ) NOT LIKE '%attachments%'

                THEN aws.supplier_key
            END
        ) AS usable_supplier_count,

        MAX(
            CASE
                WHEN aws.supplier_identity_flag =
                     'id_multiple_names_review'
                THEN 1
                ELSE 0
            END
        ) AS supplier_identity_review_flag,

        MAX(
            CASE
                WHEN aws.supplier_id_quality =
                     'unreliable_or_missing'
                THEN 1
                ELSE 0
            END
        ) AS unreliable_supplier_id_flag,

        MAX(
            CASE
                WHEN aws.canonical_supplier_name IS NOT NULL
                 AND (
                     LOWER(
                         COALESCE(
                             aws.canonical_supplier_name,
                             ''
                         )
                     ) LIKE '%successful supplier%'

                     OR LOWER(
                         COALESCE(
                             aws.canonical_supplier_name,
                             ''
                         )
                     ) LIKE '%supplier list%'

                     OR LOWER(
                         COALESCE(
                             aws.canonical_supplier_name,
                             ''
                         )
                     ) LIKE '%see webpage%'

                     OR LOWER(
                         COALESCE(
                             aws.canonical_supplier_name,
                             ''
                         )
                     ) LIKE '%contract award details%'

                     OR LOWER(
                         COALESCE(
                             aws.canonical_supplier_name,
                             ''
                         )
                     ) LIKE '%attachments%'

                     OR LOWER(
                         COALESCE(
                             aws.canonical_supplier_name,
                             ''
                         )
                     ) LIKE '%please see%'
                 )
                THEN 1
                ELSE 0
            END
        ) AS supplier_reference_text_flag

    FROM award_suppliers aws

    GROUP BY
        aws.award_id,
        aws.release_id
),

base AS (
    SELECT
        cp.award_id,
        cp.release_id,
        cp.ocid,

        p.buyer_name,
        p.procurement_category,
        p.procurement_method,

        cp.award_date,
        cp.award_value,
        cp.award_currency,

        cp.contract_start,
        cp.contract_end,
        cp.duration_years,

        COALESCE(
            ss.usable_supplier_count,
            0
        ) AS usable_supplier_count,

        COALESCE(
            ss.supplier_identity_review_flag,
            0
        ) AS supplier_identity_review_flag,

        COALESCE(
            ss.unreliable_supplier_id_flag,
            0
        ) AS unreliable_supplier_id_flag,

        COALESCE(
            ss.supplier_reference_text_flag,
            0
        ) AS supplier_reference_text_flag

    FROM contract_profiles cp

    LEFT JOIN procurements p
        ON cp.ocid = p.ocid

    LEFT JOIN supplier_summary ss
        ON cp.award_id = ss.award_id
       AND cp.release_id = ss.release_id
),

scored AS (
    SELECT
        *,

        CASE
            WHEN award_value >= 1000000000 THEN 3
            WHEN award_value >= 100000000 THEN 2
            ELSE 0
        END AS value_points,

        CASE
            WHEN duration_years >= 20 THEN 2
            WHEN duration_years >= 10 THEN 1
            ELSE 0
        END AS duration_points,

        CASE
            WHEN LOWER(
                COALESCE(procurement_method, '')
            ) = 'direct'
                THEN 2

            WHEN LOWER(
                COALESCE(procurement_method, '')
            ) = 'limited'
                THEN 1

            ELSE 0
        END AS method_points,

        CASE
            WHEN usable_supplier_count = 1
                THEN 1
            ELSE 0
        END AS single_supplier_points

    FROM base
),

final_scored AS (
    SELECT
        *,

        (
            value_points +
            duration_points +
            method_points +
            single_supplier_points
        ) AS pri_score

    FROM scored
)

SELECT
    award_id,
    release_id,
    ocid,

    buyer_name,
    procurement_category,
    procurement_method,

    award_date,

    ROUND(
        award_value,
        2
    ) AS award_value,

    award_currency,

    contract_start,
    contract_end,

    duration_years,

    usable_supplier_count,

    supplier_identity_review_flag,
    unreliable_supplier_id_flag,
    supplier_reference_text_flag,

    value_points,
    duration_points,
    method_points,
    single_supplier_points,

    pri_score,

    CASE
        WHEN pri_score >= 6
            THEN 'Priority review'

        WHEN pri_score >= 4
            THEN 'High review'

        WHEN pri_score >= 2
            THEN 'Moderate review'

        ELSE 'Lower review priority'
    END AS pri_category

FROM final_scored

WHERE pri_score >= 4

ORDER BY
    pri_score DESC,
    award_value DESC,
    duration_years DESC;

-- ============================================================
-- QUERY 17: FINAL PRI EXPORT / VALIDATION CONSISTENCY CHECK
-- ============================================================

WITH latest_awards AS (
    SELECT
        av.*,
        p.buyer_name,
        p.procurement_method,
        p.procurement_category,
        p.tender_title
    FROM award_versions av
    LEFT JOIN procurements p
        ON av.ocid = p.ocid
    WHERE av.is_latest_award_version = 1
      AND av.contract_start IS NOT NULL
      AND av.contract_end IS NOT NULL
),

supplier_summary AS (
    SELECT
        av.award_id,
        av.release_id,

        COUNT(
            DISTINCT CASE
                WHEN asup.supplier_key IS NOT NULL
                 AND asup.canonical_supplier_name IS NOT NULL
                 AND TRIM(asup.canonical_supplier_name) <> ''
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%successful supplier%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%supplier list%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%see webpage%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%contract award details%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%attachments%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%please see%'
                THEN asup.supplier_key
            END
        ) AS usable_supplier_count,

        MAX(
            CASE
                WHEN LOWER(COALESCE(asup.canonical_supplier_name, '')) LIKE '%successful supplier%'
                  OR LOWER(COALESCE(asup.canonical_supplier_name, '')) LIKE '%supplier list%'
                  OR LOWER(COALESCE(asup.canonical_supplier_name, '')) LIKE '%see webpage%'
                  OR LOWER(COALESCE(asup.canonical_supplier_name, '')) LIKE '%contract award details%'
                  OR LOWER(COALESCE(asup.canonical_supplier_name, '')) LIKE '%attachments%'
                  OR LOWER(COALESCE(asup.canonical_supplier_name, '')) LIKE '%please see%'
                THEN 1
                ELSE 0
            END
        ) AS supplier_reference_text_flag,

        MAX(
            CASE
                WHEN asup.supplier_identity_flag = 'id_multiple_names_review'
                THEN 1
                ELSE 0
            END
        ) AS supplier_identity_review_flag

    FROM latest_awards av
    LEFT JOIN award_suppliers asup
        ON av.award_id = asup.award_id
       AND av.release_id = asup.release_id

    GROUP BY
        av.award_id,
        av.release_id
),

pri_base AS (
    SELECT
        la.*,
        ss.usable_supplier_count,
        ss.supplier_reference_text_flag,
        ss.supplier_identity_review_flag,

        CASE
            WHEN la.award_value >= 1000000000 THEN 3
            WHEN la.award_value >= 100000000 THEN 2
            ELSE 0
        END AS value_points,

        CASE
            WHEN (
                julianday(la.contract_end)
                - julianday(la.contract_start)
            ) >= (20 * 365.25)
            THEN 2

            WHEN (
                julianday(la.contract_end)
                - julianday(la.contract_start)
            ) >= (10 * 365.25)
            THEN 1

            ELSE 0
        END AS duration_points,

        CASE
            WHEN LOWER(COALESCE(la.procurement_method, '')) LIKE '%direct%'
            THEN 2

            WHEN LOWER(COALESCE(la.procurement_method, '')) LIKE '%limited%'
            THEN 1

            ELSE 0
        END AS method_points,

        CASE
            WHEN ss.usable_supplier_count = 1
            THEN 1
            ELSE 0
        END AS single_supplier_points

    FROM latest_awards la
    LEFT JOIN supplier_summary ss
        ON la.award_id = ss.award_id
       AND la.release_id = ss.release_id
),

pri_final AS (
    SELECT
        *,
        (
            value_points
            + duration_points
            + method_points
            + single_supplier_points
        ) AS pri_score
    FROM pri_base
)

SELECT
    COUNT(*) AS total_records,

    SUM(
        CASE WHEN pri_score >= 6 THEN 1 ELSE 0 END
    ) AS priority_review,

    SUM(
        CASE WHEN pri_score BETWEEN 4 AND 5 THEN 1 ELSE 0 END
    ) AS high_review,

    SUM(
        CASE WHEN pri_score BETWEEN 2 AND 3 THEN 1 ELSE 0 END
    ) AS moderate_review,

    SUM(
        CASE WHEN pri_score <= 1 THEN 1 ELSE 0 END
    ) AS lower_review,

    SUM(
        CASE WHEN supplier_reference_text_flag = 1 THEN 1 ELSE 0 END
    ) AS supplier_reference_text_records,

    SUM(
        CASE WHEN supplier_identity_review_flag = 1 THEN 1 ELSE 0 END
    ) AS supplier_identity_review_records,

    SUM(
        CASE WHEN usable_supplier_count = 1 THEN 1 ELSE 0 END
    ) AS single_usable_supplier_records,

    SUM(
        CASE WHEN usable_supplier_count > 1 THEN 1 ELSE 0 END
    ) AS multiple_usable_supplier_records,

    SUM(
        CASE WHEN usable_supplier_count = 0 THEN 1 ELSE 0 END
    ) AS no_usable_supplier_records,

    SUM(
        CASE WHEN method_points > 0 THEN 1 ELSE 0 END
    ) AS procurement_method_signal_records,

    SUM(
        CASE WHEN single_supplier_points > 0 THEN 1 ELSE 0 END
    ) AS single_supplier_signal_records,

    MIN(pri_score) AS minimum_pri_score,
    MAX(pri_score) AS maximum_pri_score

FROM pri_final;

-- ============================================================
-- QUERY 18: PRI DIFFERENCE DIAGNOSTIC
-- Identify records affected by broader supplier-reference filtering
-- ============================================================

WITH latest_awards AS (
    SELECT
        av.*,
        p.buyer_name,
        p.procurement_method,
        p.procurement_category,
        p.tender_title
    FROM award_versions av
    LEFT JOIN procurements p
        ON av.ocid = p.ocid
    WHERE av.is_latest_award_version = 1
      AND av.contract_start IS NOT NULL
      AND av.contract_end IS NOT NULL
),

supplier_summary AS (
    SELECT
        av.award_id,
        av.release_id,

        COUNT(
            DISTINCT CASE
                WHEN asup.supplier_key IS NOT NULL
                 AND asup.canonical_supplier_name IS NOT NULL
                 AND TRIM(asup.canonical_supplier_name) <> ''
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%successful supplier%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%supplier list%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%see webpage%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%contract award details%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%attachments%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%please see%'
                THEN asup.supplier_key
            END
        ) AS usable_supplier_count,

        GROUP_CONCAT(
            DISTINCT asup.canonical_supplier_name
        ) AS supplier_names

    FROM latest_awards av

    LEFT JOIN award_suppliers asup
        ON av.award_id = asup.award_id
       AND av.release_id = asup.release_id

    GROUP BY
        av.award_id,
        av.release_id
),

pri_base AS (
    SELECT
        la.*,
        ss.usable_supplier_count,
        ss.supplier_names,

        CASE
            WHEN la.award_value >= 1000000000 THEN 3
            WHEN la.award_value >= 100000000 THEN 2
            ELSE 0
        END AS value_points,

        CASE
            WHEN (
                julianday(la.contract_end)
                - julianday(la.contract_start)
            ) >= (20 * 365.25)
            THEN 2

            WHEN (
                julianday(la.contract_end)
                - julianday(la.contract_start)
            ) >= (10 * 365.25)
            THEN 1

            ELSE 0
        END AS duration_points,

        CASE
            WHEN LOWER(COALESCE(la.procurement_method, '')) LIKE '%direct%'
            THEN 2

            WHEN LOWER(COALESCE(la.procurement_method, '')) LIKE '%limited%'
            THEN 1

            ELSE 0
        END AS method_points

    FROM latest_awards la

    LEFT JOIN supplier_summary ss
        ON la.award_id = ss.award_id
       AND la.release_id = ss.release_id
),

pri_final AS (
    SELECT
        *,
        (
            value_points
            + duration_points
            + method_points
            + CASE
                WHEN usable_supplier_count = 1 THEN 1
                ELSE 0
              END
        ) AS pri_score
    FROM pri_base
)

SELECT
    award_id,
    release_id,
    buyer_name,
    tender_title,
    award_value,
    procurement_method,
    contract_start,
    contract_end,
    usable_supplier_count,
    supplier_names,
    value_points,
    duration_points,
    method_points,
    CASE
        WHEN usable_supplier_count = 1 THEN 1
        ELSE 0
    END AS single_supplier_points,
    pri_score

FROM pri_final

WHERE pri_score >= 4

ORDER BY
    pri_score DESC,
    award_value DESC;

-- ============================================================
-- QUERY 19: FINAL PRI ANALYTICAL DATASET
-- Authoritative PRI calculation for Python analysis
-- ============================================================

WITH latest_awards AS (
    SELECT
        av.*,
        p.tender_title,
        p.tender_status,
        p.buyer_name,
        p.buyer_id,
        p.procurement_method,
        p.procurement_category,
        p.cpv_code,
        p.tender_value,
        p.tender_currency
    FROM award_versions av
    LEFT JOIN procurements p
        ON av.ocid = p.ocid
    WHERE av.is_latest_award_version = 1
      AND av.contract_start IS NOT NULL
      AND av.contract_end IS NOT NULL
),

supplier_summary AS (
    SELECT
        av.award_id,
        av.release_id,

        COUNT(
            DISTINCT CASE
                WHEN asup.supplier_key IS NOT NULL
                 AND asup.canonical_supplier_name IS NOT NULL
                 AND TRIM(asup.canonical_supplier_name) <> ''
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%successful supplier%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%supplier list%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%see webpage%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%contract award details%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%attachments%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%please see%'
                THEN asup.supplier_key
            END
        ) AS usable_supplier_count,

        GROUP_CONCAT(
            DISTINCT CASE
                WHEN asup.supplier_key IS NOT NULL
                 AND asup.canonical_supplier_name IS NOT NULL
                 AND TRIM(asup.canonical_supplier_name) <> ''
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%successful supplier%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%supplier list%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%see webpage%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%contract award details%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%attachments%'
                 AND LOWER(asup.canonical_supplier_name) NOT LIKE '%please see%'
                THEN asup.canonical_supplier_name
            END
        ) AS supplier_names,

        MAX(
            CASE
                WHEN LOWER(COALESCE(asup.canonical_supplier_name, '')) LIKE '%successful supplier%'
                  OR LOWER(COALESCE(asup.canonical_supplier_name, '')) LIKE '%supplier list%'
                  OR LOWER(COALESCE(asup.canonical_supplier_name, '')) LIKE '%see webpage%'
                  OR LOWER(COALESCE(asup.canonical_supplier_name, '')) LIKE '%contract award details%'
                  OR LOWER(COALESCE(asup.canonical_supplier_name, '')) LIKE '%attachments%'
                  OR LOWER(COALESCE(asup.canonical_supplier_name, '')) LIKE '%please see%'
                THEN 1
                ELSE 0
            END
        ) AS supplier_reference_text_flag,

        MAX(
            CASE
                WHEN asup.supplier_identity_flag =
                     'id_multiple_names_review'
                THEN 1
                ELSE 0
            END
        ) AS supplier_identity_review_flag

    FROM latest_awards av

    LEFT JOIN award_suppliers asup
        ON av.award_id = asup.award_id
       AND av.release_id = asup.release_id

    GROUP BY
        av.award_id,
        av.release_id
),

pri_base AS (
    SELECT
        la.*,

        COALESCE(ss.usable_supplier_count, 0)
            AS usable_supplier_count,

        ss.supplier_names,

        COALESCE(ss.supplier_reference_text_flag, 0)
            AS supplier_reference_text_flag,

        COALESCE(ss.supplier_identity_review_flag, 0)
            AS supplier_identity_review_flag,

        CASE
            WHEN la.award_value >= 1000000000 THEN 3
            WHEN la.award_value >= 100000000 THEN 2
            ELSE 0
        END AS value_points,

        CASE
            WHEN (
                julianday(la.contract_end)
                - julianday(la.contract_start)
            ) >= (20 * 365.25)
            THEN 2

            WHEN (
                julianday(la.contract_end)
                - julianday(la.contract_start)
            ) >= (10 * 365.25)
            THEN 1

            ELSE 0
        END AS duration_points,

        CASE
            WHEN LOWER(COALESCE(la.procurement_method, ''))
                 LIKE '%direct%'
            THEN 2

            WHEN LOWER(COALESCE(la.procurement_method, ''))
                 LIKE '%limited%'
            THEN 1

            ELSE 0
        END AS method_points,

        CASE
            WHEN COALESCE(ss.usable_supplier_count, 0) = 1
            THEN 1
            ELSE 0
        END AS single_supplier_points

    FROM latest_awards la

    LEFT JOIN supplier_summary ss
        ON la.award_id = ss.award_id
       AND la.release_id = ss.release_id
),

pri_final AS (
    SELECT
        *,
        (
            value_points
            + duration_points
            + method_points
            + single_supplier_points
        ) AS pri_score
    FROM pri_base
)

SELECT
    award_id,
    release_id,
    ocid,

    release_date,
    award_status,
    award_date,
    award_value,
    award_currency,
    award_title,

    contract_start,
    contract_end,

    tender_title,
    tender_status,
    buyer_name,
    buyer_id,

    procurement_method,
    procurement_category,
    cpv_code,
    tender_value,
    tender_currency,

    ROUND(
        (
            julianday(contract_end)
            - julianday(contract_start)
        ),
        2
    ) AS contract_duration_days,

    ROUND(
        (
            julianday(contract_end)
            - julianday(contract_start)
        ) / 365.25,
        2
    ) AS contract_duration_years,

    usable_supplier_count,
    supplier_names,
    supplier_reference_text_flag,
    supplier_identity_review_flag,

    value_points,
    duration_points,
    method_points,
    single_supplier_points,

    pri_score,

    CASE
        WHEN pri_score >= 6
            THEN 'Priority review'

        WHEN pri_score >= 4
            THEN 'High review'

        WHEN pri_score >= 2
            THEN 'Moderate review'

        ELSE 'Lower review priority'
    END AS pri_category,

    CASE
        WHEN pri_score >= 6
            THEN 'Multiple material screening signals'

        WHEN pri_score >= 4
            THEN 'Several material screening signals'

        WHEN pri_score >= 2
            THEN 'At least one material screening signal'

        ELSE 'Limited screening signals'
    END AS review_rationale

FROM pri_final

ORDER BY
    pri_score DESC,
    award_value DESC;