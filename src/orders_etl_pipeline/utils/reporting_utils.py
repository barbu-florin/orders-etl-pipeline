from sqlalchemy import Engine, text
from orders_etl_pipeline.config import get_logger

logger = get_logger(__name__)


def log_bronze_layer(engine: Engine) -> None:
    with engine.connect() as conn:
        orders_raw_count = conn.execute(text("""
            SELECT COUNT(*)
            FROM bronze.orders_raw
        """)).scalar()

        fx_rates_raw_count = conn.execute(text("""
            SELECT COUNT(*)
            FROM bronze.fx_rates_raw
        """)).scalar()

    logger.info("Bronze layer counts:")
    logger.info("- bronze.orders_raw: %s", orders_raw_count)
    logger.info("- bronze.fx_rates_raw: %s", fx_rates_raw_count)


def log_silver_layer(engine: Engine) -> None:
    with engine.connect() as conn:
        orders_clean_count = conn.execute(text("""
            SELECT COUNT(*)
            FROM silver.orders_clean
        """)).scalar()

        orders_failed_count = conn.execute(text("""
            SELECT COUNT(*)
            FROM silver.orders_failed
        """)).scalar()

        fx_rates_count = conn.execute(text("""
            SELECT COUNT(*)
            FROM silver.fx_rates
        """)).scalar()

    logger.info("Silver layer counts:")
    logger.info("- silver.orders_clean: %s", orders_clean_count)
    logger.info("- silver.orders_failed: %s", orders_failed_count)
    logger.info("- silver.fx_rates: %s", fx_rates_count)


def log_top_customers(engine: Engine) -> None:
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT customer_id, total_spend_in_eur
            FROM gold.customer_spend_eur
            ORDER BY total_spend_in_eur DESC
            LIMIT 10
        """)).fetchall()

    logger.info("Top 10 customers by spend:")
    for customer_id, spend in rows:
        logger.info("('%s', %s)", customer_id, spend)


def log_country_revenue_summary(engine: Engine) -> None:
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT country, revenue_in_eur
            FROM gold.country_category_breakdown
            ORDER BY revenue_in_eur DESC
        """)).fetchall()

    logger.info("%d countries above the EUR 40,000 threshold:", len(rows))

    for country, revenue in rows:
        logger.info("('%s', %s)", country, revenue)
