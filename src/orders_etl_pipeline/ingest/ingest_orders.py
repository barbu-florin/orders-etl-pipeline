from sqlalchemy import Engine

from orders_etl_pipeline.extract import fetch_api_data
from orders_etl_pipeline.load import load_to_db
from orders_etl_pipeline.config import ORDERS_HEADER, ORDERS_URL, get_logger

logger = get_logger(__name__)


def ingest_orders(engine: Engine):
    orders_raw = fetch_api_data(ORDERS_URL, ORDERS_HEADER)
    load_to_db(orders_raw, engine, "orders_raw", "bronze")
