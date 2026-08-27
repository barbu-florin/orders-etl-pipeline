import pandas as pd


def fix_quantities(df: pd.DataFrame) -> pd.DataFrame:
    df["qty"] = df["qty"].abs()
    return df


def fix_customer_ids(df: pd.DataFrame) -> pd.DataFrame:
    missing = df["customer_id"].isna()

    extracted_ids = (
        df.loc[missing, "customer_email"]
        .str.extract(r"^customer(\d+)@example\.com$")[0]
    )

    tester_ids = (
        df.loc[missing, "customer_email"]
        .str.extract(r"^internal\.tester(\d+)@aqurate\.ai$")[0]
    )

    extracted_ids = extracted_ids.fillna(tester_ids)

    df.loc[missing, "customer_id"] = pd.to_numeric(
        extracted_ids,
        errors="coerce"
    )

    return df


def fix_categories(df: pd.DataFrame) -> pd.DataFrame:
    category_mapping = (
        df
        .dropna(subset=["category", "sku"])
        .drop_duplicates("sku")
        .set_index("sku")["category"]
    )

    df["category"] = df["category"].fillna(
        df["sku"].map(category_mapping)
    )

    return df

def normalize_order_ts(df: pd.DataFrame) -> pd.DataFrame:
    normalized = []

    for value in df["order_ts"]:
        value = str(value).strip()

        if value.isnumeric():
            parsed = pd.to_datetime(int(value), unit="s")

        elif "T" in value:
            parsed = pd.to_datetime(value, errors="coerce")

        else:
            parsed = pd.to_datetime(
                value,
                dayfirst=True,
                errors="coerce"
            )

        normalized.append(parsed)

    df["order_ts"] = normalized

    return df

def fix_invalid_unit_prices(df: pd.DataFrame) -> pd.DataFrame:
    invalid = df["unit_price"].isin([0, 999999])

    group_columns = [
        "sku",
        "currency",
        "fx_reference_date",
    ]

    average_prices = (
        df.loc[~invalid]
        .groupby(group_columns)["unit_price"]
        .mean()
    )

    for index in df.index[invalid]:
        row = df.loc[index]

        key = (
            row["sku"],
            row["currency"],
            row["fx_reference_date"],
        )

        if key in average_prices.index:
            df.loc[index, "unit_price"] = average_prices.loc[key]
        else:
            df.loc[index, "unit_price"] = pd.NA

    return df

def fix_sku(df: pd.DataFrame) -> pd.DataFrame:
    df["sku"] = df["sku"].replace({
        "SKU-FA-O03": "SKU-FA-003",
        "SKUEL001": "SKU-EL-001",
    })

    df["sku"] = df["sku"].str.replace(" ", "-", regex=False)

    return df


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = fix_customer_ids(df)
    df = normalize_order_ts(df)
    df = fix_sku(df)
    df = fix_categories(df)
    df = fix_quantities(df)
    df = fix_invalid_unit_prices(df)

    return df