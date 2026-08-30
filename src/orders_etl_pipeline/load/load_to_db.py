from sqlalchemy import Engine
import pandas as pd
from orders_etl_pipeline.config import get_logger

logger = get_logger(__name__)


def load_to_db(df: pd.DataFrame, engine: Engine, table: str, schema: str) -> None:
    df.to_sql(
        table,
        con=engine,
        schema=schema,
        if_exists="replace",
        index=False,
    )
