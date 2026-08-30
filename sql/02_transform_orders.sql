-- Clean order IDs
CREATE OR REPLACE FUNCTION fix_order_id(order_id TEXT)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT NULLIF(
        UPPER(TRIM(order_id)),
        ''
    );
$$;


-- Make quantities positive
CREATE OR REPLACE FUNCTION fix_quantity(qty BIGINT)
RETURNS INTEGER
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT CASE
        WHEN qty IS NULL THEN NULL
        ELSE ABS(qty)::INTEGER
    END;
$$;


-- Normalize timestamps
CREATE OR REPLACE FUNCTION normalise_order_ts(order_ts TEXT)
RETURNS TIMESTAMP
LANGUAGE plpgsql
AS $$
DECLARE
    value TEXT;
BEGIN
    value := TRIM(COALESCE(order_ts, ''));

    IF value = '' THEN
        RETURN NULL;
    END IF;

    -- Unix timestamp
    IF value ~ '^[0-9]+$' THEN
        RETURN TO_TIMESTAMP(value::BIGINT) AT TIME ZONE 'UTC';

    -- ISO timestamp
    ELSIF value ~ '^\d{4}-\d{2}-\d{2}T' THEN
        RETURN value::TIMESTAMP;

    -- Day-first date
    ELSIF value ~ '^\d{1,2}/\d{1,2}/\d{4}' THEN
        RETURN TO_TIMESTAMP(
            value,
            CASE
                WHEN value ~ ' ' THEN 'DD/MM/YYYY HH24:MI'
                ELSE 'DD/MM/YYYY'
            END
        );
    END IF;

    RETURN NULL;

EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$;


-- Recover missing customer IDs from known email patterns
CREATE OR REPLACE FUNCTION fix_customer_id(customer_id DOUBLE PRECISION, email TEXT)
RETURNS NUMERIC
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT COALESCE(
        customer_id,
        CASE
            WHEN LOWER(TRIM(email)) ~ '^customer[0-9]+@example\.com$'
                THEN SUBSTRING(
                    LOWER(TRIM(email))
                    FROM '[0-9]+'
                )::NUMERIC

            WHEN LOWER(TRIM(email)) ~ '^internal\.tester[0-9]+@aqurate\.ai$'
                THEN SUBSTRING(
                    LOWER(TRIM(email))
                    FROM '[0-9]+'
                )::NUMERIC

            ELSE NULL
        END
    );
$$;


-- Normalize SKUs
CREATE OR REPLACE FUNCTION normalise_sku(sku TEXT)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT CASE
        WHEN cleaned IS NULL THEN NULL

        WHEN LENGTH(cleaned) = 8 THEN
            SUBSTRING(cleaned, 1, 3)
            || '-'
            || SUBSTRING(cleaned, 4, 2)
            || '-'
            || SUBSTRING(cleaned, 6, 3)

        ELSE cleaned
    END
    FROM (
        SELECT NULLIF(
            REGEXP_REPLACE(
                UPPER(COALESCE(sku, '')),
                '[^A-Z0-9]',
                '',
                'g'
            ),
            ''
        ) AS cleaned
    ) s;
$$;

TRUNCATE TABLE silver.orders_clean;
TRUNCATE TABLE silver.orders_failed;

DROP TABLE IF EXISTS temp_orders;

CREATE TEMP TABLE temp_orders AS
SELECT
    fix_order_id(r.order_id) AS order_id,
    fix_customer_id(r.customer_id, r.customer_email) AS customer_id,
    NULLIF(LOWER(TRIM(r.customer_email)), '') AS customer_email,
    normalise_order_ts(r.order_ts) AS order_ts,
    LOWER(TRIM(r.status)) AS status,
    LOWER(TRIM(r.channel)) AS channel,
    normalise_sku(r.sku) AS sku,
    NULLIF(TRIM(r.product_name), '') AS product_name,
    NULLIF(TRIM(r.category), '') AS category,
    fix_quantity(r.qty) AS qty,
    r.unit_price::NUMERIC AS unit_price,
    NULLIF(UPPER(TRIM(r.currency)), '') AS currency,
    NULLIF(UPPER(TRIM(r.country)), '') AS country,
    r.fx_reference_date::DATE AS fx_reference_date
FROM bronze.orders_raw AS r;

DROP TABLE IF EXISTS temp_sku_categories;

CREATE TEMP TABLE temp_sku_categories AS
SELECT
    normalise_sku(sku) AS sku,
    category
FROM (
    SELECT
        normalise_sku(sku) AS sku,
        TRIM(category) AS category,
        COUNT(*) AS category_count,
        ROW_NUMBER() OVER (
            PARTITION BY normalise_sku(sku)
            ORDER BY
                COUNT(*) DESC,
                TRIM(category) ASC
        ) AS row_number
    FROM bronze.orders_raw
    WHERE NULLIF(TRIM(category), '') IS NOT NULL
    GROUP BY
        normalise_sku(sku),
        TRIM(category)
) categories
WHERE row_number = 1;

DROP TABLE IF EXISTS temp_orders_with_category;

CREATE TEMP TABLE temp_orders_with_category AS
SELECT
    o.order_id,
    o.customer_id,
    o.customer_email,
    o.order_ts,
    o.status,
    o.channel,
    o.sku,
    o.product_name,
    COALESCE(o.category, c.category) AS category,
    o.qty,
    o.unit_price,
    o.currency,
    o.country,
    o.fx_reference_date
FROM temp_orders AS o
LEFT JOIN temp_sku_categories AS c
    ON c.sku = o.sku;

DROP TABLE IF EXISTS temp_deduplicated;

CREATE TEMP TABLE temp_deduplicated AS
SELECT
    o.*,
    ROW_NUMBER() OVER (
        PARTITION BY order_id, sku
        ORDER BY
            fx_reference_date ASC NULLS LAST,
            order_ts ASC NULLS LAST,
            customer_email ASC NULLS LAST
    ) AS row_number
FROM temp_orders_with_category AS o;

DROP TABLE IF EXISTS temp_validated;

CREATE TEMP TABLE temp_validated AS
SELECT
    d.*,
    CASE
        WHEN order_id IS NULL THEN 'order_id is missing'
        WHEN customer_email IS NULL THEN 'customer_email is missing'
        WHEN sku IS NULL THEN 'sku is missing'
        WHEN category IS NULL THEN 'category is missing'
        WHEN order_ts IS NULL THEN 'order_ts is invalid'
        WHEN customer_id IS NULL THEN 'customer_id is missing'
        WHEN qty IS NULL OR qty = 0 THEN 'qty is invalid'
        WHEN unit_price = 999999 THEN 'Unusual unit_price'
        WHEN currency IS NULL THEN 'currency is missing'
        WHEN country IS NULL THEN 'country is missing'
        WHEN fx_reference_date IS NULL THEN 'fx_reference_date is invalid'
        WHEN LOWER(TRIM(customer_email)) LIKE 'internal.tester%@aqurate.ai'
            THEN 'order is a test'
        ELSE NULL
    END AS reason_of_rejection
FROM temp_deduplicated AS d;

INSERT INTO silver.orders_clean
SELECT
    order_id,
    customer_id,
    customer_email,
    order_ts,
    status,
    channel,
    sku,
    product_name,
    category,
    qty,
    unit_price,
    currency,
    country,
    fx_reference_date
FROM temp_validated
WHERE reason_of_rejection IS NULL
  AND row_number = 1;

INSERT INTO silver.orders_failed
SELECT
    order_id,
    customer_id,
    customer_email,
    order_ts,
    status,
    channel,
    sku,
    product_name,
    category,
    qty,
    unit_price,
    currency,
    country,
    fx_reference_date,
    CASE
        WHEN reason_of_rejection IS NOT NULL THEN reason_of_rejection
        WHEN row_number > 1 THEN 'order_line is duplicated'
    END AS reason_of_rejection
FROM temp_validated
WHERE reason_of_rejection IS NOT NULL
   OR row_number > 1;