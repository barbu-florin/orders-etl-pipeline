from sqlalchemy import Engine

from orders_etl_pipeline.extract import fetch_api_data
from orders_etl_pipeline.load import load_to_db
from orders_etl_pipeline.utils import get_required_currencies, get_fx_date_range
from orders_etl_pipeline.config import FX_HEADER, FX_URL, get_logger

logger = get_logger(__name__)


def ingest_fx_rates(engine: Engine):
    currencies = get_required_currencies(engine)
    start_date, end_date = get_fx_date_range(engine)
    params = {
        "base": "EUR",
        "quotes": ",".join(currencies),
        "from": start_date,
        "to": end_date,
    }
    fx_rates_raw = fetch_api_data(FX_URL, FX_HEADER, params)
    load_to_db(fx_rates_raw, engine, "fx_rates_raw", "bronze")
