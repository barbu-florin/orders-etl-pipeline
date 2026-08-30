CREATE OR REPLACE VIEW silver.vw_orders_clean_eur AS
SELECT
    o.*,
    CASE
        WHEN o.currency = 'EUR' THEN 1
        ELSE fx.rate
    END AS fx_rate_used,
    fx.rate_date AS fx_rate_date_used,
    CASE
        WHEN o.currency = 'EUR'
            THEN o.qty * o.unit_price
        WHEN fx.rate IS NULL
            THEN NULL
        ELSE ROUND((o.qty * o.unit_price) / fx.rate, 2)
    END AS amount_in_eur
FROM silver.orders_clean AS o
LEFT JOIN LATERAL (
    SELECT
        r.date AS rate_date,
        r.rate
    FROM silver.fx_rates AS r
    WHERE r.base = 'EUR'
      AND r.quote = o.currency
      AND r.date <= o.fx_reference_date
    ORDER BY r.date DESC
    LIMIT 1
) AS fx
    ON o.currency <> 'EUR';