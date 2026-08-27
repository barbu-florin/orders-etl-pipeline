import pandas as pd
from sqlalchemy import Engine


def load_to_db(df: pd.DataFrame, engine: Engine, table: str, schema: str) -> None:
    df.to_sql(
        table,
        con=engine,
        schema=schema,
        if_exists="replace",
        index=False,
    )