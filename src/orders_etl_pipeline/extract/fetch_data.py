import requests
import pandas as pd

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from orders_etl_pipeline.config import get_logger

logger = get_logger(__name__)


def fetch_api_data(url, headers=None, params=None):
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    with requests.Session() as session:
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        try:
            response = session.get(
                url,
                params=params,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

        except requests.RequestException:
            logger.exception("HTTP request failed for %s", url)
            raise

    data = response.json()
    df = pd.DataFrame(data)

    return df
