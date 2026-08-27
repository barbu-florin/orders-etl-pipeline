import requests
import pandas as pd

def fetch_api_data(url, headers=None):
    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    return pd.DataFrame(response.json())