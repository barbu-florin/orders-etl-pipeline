CREATE SCHEMA IF NOT EXISTS bronze;

CREATE SCHEMA IF NOT EXISTS silver;

CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE IF NOT EXISTS silver.orders_clean (
    order_id TEXT,
    customer_id INTEGER,
    customer_email TEXT,
    order_ts TIMESTAMP,
    status TEXT,
    channel TEXT,
    sku TEXT,
    product_name TEXT,
    category TEXT,
    qty INTEGER,
    unit_price DECIMAL,
    currency TEXT,
    country TEXT,
    fx_reference_date DATE
);

CREATE TABLE IF NOT EXISTS silver.orders_failed (
    order_id TEXT,
    customer_id INTEGER,
    customer_email TEXT,
    order_ts TIMESTAMP,
    status TEXT,
    channel TEXT,
    sku TEXT,
    product_name TEXT,
    category TEXT,
    qty INTEGER,
    unit_price DECIMAL,
    currency TEXT,
    country TEXT,
    fx_reference_date DATE,
    reject_reason TEXT
);

CREATE TABLE IF NOT EXISTS silver.fx_rates (date DATE, base TEXT, quote TEXT, rate NUMERIC);