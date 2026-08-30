from pathlib import Path
from sqlalchemy import create_engine, text, Engine
from orders_etl_pipeline.config import get_logger, TARGET_DB_URL

logger = get_logger(__name__)


def get_engine() -> Engine:
    if not TARGET_DB_URL:
        logger.error("TARGET_DB_URL is not configured")
        raise ValueError("TARGET_DB_URL is not configured")

    return create_engine(TARGET_DB_URL)


def execute_sql_file(engine: Engine, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.execute(text(sql))
