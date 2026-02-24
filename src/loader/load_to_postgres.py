import pandas as pd
from src.utils.db import pg_engine

def load_parquet(table_name: str, parquet_path: str, schema: str = "bronze"):
    engine = pg_engine()
    df = pd.read_parquet(parquet_path)

    df.to_sql(
        table_name,
        engine,
        schema=schema,
        if_exists="replace",
        index=False,
        chunksize=20000,
        method="multi"
    )

    print(f"✅ Loaded {schema}.{table_name} rows={len(df)}")


if __name__ == "__main__":
    load_parquet("users", "data/users.parquet")
    load_parquet("merchants", "data/merchants.parquet")
    load_parquet("devices", "data/devices.parquet")
    load_parquet("payment_attempts", "data/payment_attempts.parquet")