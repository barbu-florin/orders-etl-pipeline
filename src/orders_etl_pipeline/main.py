from orders_etl_pipeline.db import execute_sql_file, get_engine
from orders_etl_pipeline.config import SQL_DIR, configure_logging, get_logger
from orders_etl_pipeline.ingest import ingest_fx_rates, ingest_orders
from orders_etl_pipeline.utils import (
    log_country_revenue_summary,
    log_top_customers,
    log_bronze_layer,
    log_silver_layer,
)

logger = get_logger(__name__)


def main():
    configure_logging()
    logger.info("ETL pipeline started")

    try:
        engine = get_engine()

        # SETUP
        logger.info("Running schema setup")
        execute_sql_file(engine, SQL_DIR / "01_schema_setup.sql")

        # BRONZE LAYER - RAW DATA INGESTION
        ingest_orders(engine)
        ingest_fx_rates(engine)
        log_bronze_layer(engine)

        # SILVER LAYER - DATA CLEANING AND TRANSFORMATION
        logger.info("Running silver layer transformations")
        execute_sql_file(engine, SQL_DIR / "02_transform_orders.sql")
        execute_sql_file(engine, SQL_DIR / "03_transform_fx_rates.sql")
        log_silver_layer(engine)

        # INTERMEDIATE LAYER - APPLY FX RATES AND CALCULATE EUR VALUES ONLY ONCE
        logger.info("Creating EUR-clean intermediate view")
        execute_sql_file(engine, SQL_DIR / "04_vw_orders_clean_eur.sql")

        # GOLD LAYER - BUSINESS REPORTING
        logger.info("Running gold layer reporting queries")
        execute_sql_file(engine, SQL_DIR / "05_customer_spend_eur.sql")
        log_top_customers(engine)

        execute_sql_file(engine, SQL_DIR / "06_country_category_breakdown.sql")
        log_country_revenue_summary(engine)

        logger.info("ETL pipeline completed successfully")
    except Exception:
        logger.exception("ETL pipeline failed")
        raise


if __name__ == "__main__":
    main()
