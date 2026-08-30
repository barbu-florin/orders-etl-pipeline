from datetime import date, timedelta

from sqlalchemy import text, Engine


def get_required_currencies(engine: Engine) -> list[str]:
    with engine.connect() as conn:
        currencies = [row[0] for row in conn.execute(text("""
                    SELECT DISTINCT currency
                    FROM bronze.orders_raw
                    WHERE currency IS NOT NULL
                      AND UPPER(TRIM(currency)) <> 'EUR'
                """))]

    return sorted({currency.strip().upper() for currency in currencies if currency})


def get_fx_date_range(
    engine: Engine,
    lookback_days: int = 7,
) -> tuple[str, str]:

    with engine.connect() as conn:
        min_date, max_date = conn.execute(text("""
                SELECT
                    MIN(fx_reference_date),
                    MAX(fx_reference_date)
                FROM bronze.orders_raw
            """)).one()

    if min_date is None or max_date is None:
        raise ValueError("No FX reference dates found in bronze.orders_raw")

    min_date = date.fromisoformat(min_date)
    max_date = date.fromisoformat(max_date)

    start_date = min_date - timedelta(days=lookback_days)
    end_date = min(max_date, date.today())

    return start_date.isoformat(), end_date.isoformat()
