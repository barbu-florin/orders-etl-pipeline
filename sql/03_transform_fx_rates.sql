TRUNCATE TABLE silver.fx_rates;

INSERT INTO silver.fx_rates (
    date,
    base,
    quote,
    rate
)
SELECT
    date::DATE,
    UPPER(BTRIM(base)),
    UPPER(BTRIM(quote)),
    rate::NUMERIC
FROM bronze.fx_rates_raw;