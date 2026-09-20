-- ============================================================
-- SUPPLIER PRI DIAGNOSTIC
-- ============================================================

-- 1. How many latest awards have supplier relationships?

SELECT
    COUNT(DISTINCT av.award_id) AS latest_awards,
    COUNT(DISTINCT aws.award_id) AS awards_with_supplier_relationships
FROM award_versions av
LEFT JOIN award_suppliers aws
    ON av.award_id = aws.award_id
   AND av.release_id = aws.release_id
WHERE av.is_latest_award_version = 1;


-- 2. Supplier relationship quality

SELECT
    COUNT(*) AS relationship_rows,

    COUNT(
        CASE
            WHEN aws.canonical_supplier_name IS NOT NULL
            THEN 1
        END
    ) AS with_canonical_name,

    COUNT(
        CASE
            WHEN aws.supplier_key IS NOT NULL
            THEN 1
        END
    ) AS with_supplier_key,

    COUNT(
        CASE
            WHEN aws.supplier_identity_flag = 0
            THEN 1
        END
    ) AS identity_flag_zero,

    COUNT(
        CASE
            WHEN aws.supplier_identity_flag = 1
            THEN 1
        END
    ) AS identity_flag_one,

    COUNT(
        CASE
            WHEN aws.identity_review_flag = 1
            THEN 1
        END
    ) AS identity_review_flag_one

FROM award_suppliers aws;


-- 3. Supplier counts per latest award

WITH latest_awards AS (
    SELECT
        award_id,
        release_id
    FROM award_versions
    WHERE is_latest_award_version = 1
),

supplier_counts AS (
    SELECT
        la.award_id,
        la.release_id,

        COUNT(*) AS relationship_rows,

        COUNT(
            DISTINCT aws.supplier_key
        ) AS supplier_keys,

        COUNT(
            DISTINCT CASE
                WHEN aws.canonical_supplier_name IS NOT NULL
                THEN aws.supplier_key
            END
        ) AS named_supplier_keys

    FROM latest_awards la

    LEFT JOIN award_suppliers aws
        ON la.award_id = aws.award_id
       AND la.release_id = aws.release_id

    GROUP BY
        la.award_id,
        la.release_id
)

SELECT
    COUNT(*) AS latest_awards,

    SUM(
        CASE
            WHEN relationship_rows > 0
            THEN 1
            ELSE 0
        END
    ) AS awards_with_relationship_rows,

    SUM(
        CASE
            WHEN supplier_keys > 0
            THEN 1
            ELSE 0
        END
    ) AS awards_with_supplier_keys,

    SUM(
        CASE
            WHEN named_supplier_keys > 0
            THEN 1
            ELSE 0
        END
    ) AS awards_with_named_supplier_keys,

    SUM(
        CASE
            WHEN named_supplier_keys = 1
            THEN 1
            ELSE 0
        END
    ) AS awards_with_one_named_supplier

FROM supplier_counts;


-- 4. Inspect the exact supplier fields for known review candidates

WITH latest_awards AS (
    SELECT
        award_id,
        release_id,
        ocid,
        award_value
    FROM award_versions
    WHERE is_latest_award_version = 1
)

SELECT
    la.award_id,
    la.ocid,
    la.award_value,

    aws.supplier_id,
    aws.supplier_name,
    aws.canonical_supplier_name,
    aws.supplier_key,
    aws.supplier_id_quality,
    aws.supplier_identity_flag,
    aws.identity_review_flag

FROM latest_awards la

JOIN award_suppliers aws
    ON la.award_id = aws.award_id
   AND la.release_id = aws.release_id

WHERE la.award_value >= 1000000000

ORDER BY
    la.award_value DESC

LIMIT 50;