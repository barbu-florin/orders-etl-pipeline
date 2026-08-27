import os

from dotenv import load_dotenv

from orders_etl_pipeline.extract.fetch_data import fetch_api_data
from orders_etl_pipeline.database.connection import get_engine
from orders_etl_pipeline.load.load_to_db import load_to_db
from orders_etl_pipeline.transform.clean_orders import clean_orders

load_dotenv()


def main():
    engine = get_engine()

    orders_url = "https://jzozteoirwfczccltcdr.supabase.co/rest/v1/orders_raw"
    fx_url = "https://api.frankfurter.dev/v2/rates"

    orders_headers = {
        "Content-Type": "application/json",
        "apikey": os.getenv("API_KEY"),
    }

    fx_headers = {
        "Content-Type": "application/json",
    }

    orders_raw_df = fetch_api_data(orders_url, orders_headers)

    load_to_db(
        orders_raw_df,
        engine,
        table="orders_raw",
        schema="bronze",
    )

    orders_clean_df = clean_orders(orders_raw_df)

    load_to_db(
        orders_clean_df,
        engine,
        table="orders_clean",
        schema="silver"
    )

    fx_rates = fetch_api_data(fx_url, fx_headers)

    load_to_db(fx_rates, engine, table="fx_rates", schema="silver")




if __name__ == "__main__":
    main()